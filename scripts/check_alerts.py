"""Script autonome (sans Streamlit) pour vérifier les alertes de toute la watchlist et
notifier Telegram. Destiné à être exécuté périodiquement (déclenchement externe recommandé,
voir README) — ne s'exécute que pendant la fenêtre horaire de marché configurée.

Les alertes de croisement/contact/RSI sont basées sur un CHANGEMENT D'ÉTAT (persisté dans
alerts_state.json, par titre) pour ne jamais manquer un événement survenu entre deux
vérifications, ni spammer tant que l'état reste inchangé.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data import get_daily, get_h1, get_m5, get_current_price
from utils.indicators import add_emas, rsi
from utils.telegram_utils import send_telegram_message
from utils.watchlist import load_watchlist
from utils.market_hours import is_market_hours
from utils.alerts_store import (
    load_alerts_config,
    load_alerts_state,
    save_alerts_state,
    get_ticker_config,
    get_ticker_state,
    ALERT_TOGGLE_KEYS,
)


def ema_relation(df):
    if df.empty:
        return None
    df = add_emas(df, (8, 20))
    last = df.iloc[-1]
    if last["EMA8"] != last["EMA8"] or last["EMA20"] != last["EMA20"]:
        return None
    return "above" if last["EMA8"] > last["EMA20"] else "below"


def check_touch(df, ema_col, tol_pct=0.3):
    if df.empty:
        return False
    df = add_emas(df, (8, 20, 50, 200))
    last = df.iloc[-1]
    ema_val = last[ema_col]
    if ema_val != ema_val or ema_val == 0:
        return False
    return bool(last["Low"] <= ema_val <= last["High"] or abs(last["Close"] - ema_val) / ema_val * 100 <= tol_pct)


def check_one_ticker(ticker, cfg, state):
    messages = []

    price = get_current_price(ticker)
    suffix = f" | Prix actuel : {price:.2f} €" if price is not None else ""

    def handle_cross(enabled, df, state_key, label):
        if not enabled:
            return
        rel = ema_relation(df)
        if rel is None:
            return
        prev_rel = state.get(state_key)
        if prev_rel is not None and rel != prev_rel:
            direction = "haussier ↑" if rel == "above" else "baissier ↓"
            messages.append(f"Croisement EMA8/EMA20 {direction} détecté en {label} sur {ticker}{suffix}")
        state[state_key] = rel

    df_m5 = get_m5(ticker, "5d")
    handle_cross(cfg["cross_ema_m5"], df_m5, "m5_ema_cross", "M5")

    df_h1 = get_h1(ticker, "60d")
    handle_cross(cfg["cross_ema_h1"], df_h1, "h1_ema_cross", "H1")

    df_d1 = get_daily(ticker)
    handle_cross(cfg["cross_ema_d1"], df_d1, "d1_ema_cross", "D1")

    def handle_touch(enabled, ema_col, state_key, label):
        if not enabled:
            return
        touching = check_touch(df_d1, ema_col)
        if touching and not state.get(state_key, False):
            messages.append(f"La dernière bougie D1 touche l'{label} sur {ticker}{suffix}")
        state[state_key] = touching

    handle_touch(cfg["touch_ema20_d1"], "EMA20", "d1_touch_ema20", "EMA20")
    handle_touch(cfg["touch_ema50_d1"], "EMA50", "d1_touch_ema50", "EMA50")
    handle_touch(cfg["touch_ema200_d1"], "EMA200", "d1_touch_ema200", "EMA200")

    def handle_rsi(enabled, df, state_key, label, high_th=70, low_th=30):
        if not enabled or df.empty:
            return
        r = rsi(df["Close"]).iloc[-1]
        zone = "overbought" if r > high_th else "oversold" if r < low_th else "neutral"
        prev_zone = state.get(state_key, "neutral")
        if zone != prev_zone and zone != "neutral":
            zone_label = f"surachat (>{high_th})" if zone == "overbought" else f"survente (<{low_th})"
            messages.append(f"RSI {label} = {r:.1f} — entrée en zone de {zone_label} sur {ticker}{suffix}")
        state[state_key] = zone

    handle_rsi(cfg["rsi_d1"], df_d1, "d1_rsi_zone", "D1")
    handle_rsi(cfg.get("rsi_m5", False), df_m5, "m5_rsi_zone", "M5")
    handle_rsi(
        cfg.get("rsi_h1", False),
        df_h1,
        "h1_rsi_zone",
        "H1",
        high_th=cfg.get("rsi_h1_high", 67) or 67,
        low_th=cfg.get("rsi_h1_low", 33) or 33,
    )

    if cfg["volume_spike_d1"] and not df_d1.empty:
        vol_avg20 = df_d1["Volume"].tail(20).mean()
        vol_jour = df_d1["Volume"].iloc[-1]
        today_str = str(df_d1.index[-1].date())
        spike = bool(vol_avg20 and vol_jour > 1.5 * vol_avg20)
        if spike and state.get("d1_volume_spike_date") != today_str:
            messages.append(f"Volume journalier = {vol_jour / vol_avg20:.2f}x la moyenne 20j sur {ticker}{suffix}")
            state["d1_volume_spike_date"] = today_str
        elif not spike:
            state["d1_volume_spike_date"] = None

    if cfg["price_alert_enabled"] and price is not None:
        high = cfg.get("price_high") or 0
        low = cfg.get("price_low") or 0
        if high:
            above = price >= high
            if above and not state.get("price_above_high", False):
                messages.append(f"Prix de {ticker} = {price:.2f} € — seuil HAUT {high:.2f} € atteint")
            state["price_above_high"] = above
        if low:
            below = price <= low
            if below and not state.get("price_below_low", False):
                messages.append(f"Prix de {ticker} = {price:.2f} € — seuil BAS {low:.2f} € atteint")
            state["price_below_low"] = below

    return messages


def main():
    if not is_market_hours():
        print("Hors des heures de marché configurées (lun-ven 8h30-17h45 Paris) — vérification ignorée.")
        return

    watchlist = load_watchlist()
    cfg_all = load_alerts_config()
    state_all = load_alerts_state()

    tickers = sorted(set(watchlist) | set(cfg_all.keys()))
    total_sent = 0
    checked = 0

    for ticker in tickers:
        cfg = get_ticker_config(cfg_all, ticker)
        if not any(cfg.get(k) for k in ALERT_TOGGLE_KEYS):
            continue
        checked += 1
        state = get_ticker_state(state_all, ticker)
        messages = check_one_ticker(ticker, cfg, state)
        state_all[ticker] = state

        for m in messages:
            ok, info = send_telegram_message(f"🔔 {m}")
            print(("OK  " if ok else "FAIL"), m, "" if ok else info)
            if ok:
                total_sent += 1

    save_alerts_state(state_all)
    print(f"{total_sent} alerte(s) envoyée(s) sur {checked} titre(s) avec alertes actives.")


if __name__ == "__main__":
    main()
