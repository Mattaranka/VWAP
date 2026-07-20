"""Script autonome (sans Streamlit) pour vérifier les alertes de toute la watchlist et
notifier Telegram. Destiné à être exécuté périodiquement par GitHub Actions.

Les alertes de croisement/contact/RSI sont basées sur un CHANGEMENT D'ÉTAT (persisté dans
alerts_state.json, par titre) pour ne jamais manquer un croisement survenu entre deux
vérifications, ni spammer tant que l'état reste inchangé. L'alerte de volume utilise la
date du jour pour ne se déclencher qu'une fois par séance.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data import get_daily, get_h1, get_m5
from utils.indicators import add_emas, rsi
from utils.telegram_utils import send_telegram_message
from utils.watchlist import load_watchlist
from utils.alerts_store import (
    load_alerts_config,
    load_alerts_state,
    save_alerts_state,
    get_ticker_config,
    get_ticker_state,
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

    def handle_cross(enabled, df, state_key, label):
        if not enabled:
            return
        rel = ema_relation(df)
        if rel is None:
            return
        prev_rel = state.get(state_key)
        if prev_rel is not None and rel != prev_rel:
            direction = "haussier ↑" if rel == "above" else "baissier ↓"
            messages.append(f"Croisement EMA8/EMA20 {direction} détecté en {label} sur {ticker}")
        state[state_key] = rel

    handle_cross(cfg["cross_ema_m5"], get_m5(ticker, "5d"), "m5_ema_cross", "M5")
    handle_cross(cfg["cross_ema_h1"], get_h1(ticker, "60d"), "h1_ema_cross", "H1")

    df_d1 = get_daily(ticker)
    handle_cross(cfg["cross_ema_d1"], df_d1, "d1_ema_cross", "D1")

    def handle_touch(enabled, ema_col, state_key, label):
        if not enabled:
            return
        touching = check_touch(df_d1, ema_col)
        if touching and not state.get(state_key, False):
            messages.append(f"La dernière bougie D1 touche l'{label} sur {ticker}")
        state[state_key] = touching

    handle_touch(cfg["touch_ema20_d1"], "EMA20", "d1_touch_ema20", "EMA20")
    handle_touch(cfg["touch_ema50_d1"], "EMA50", "d1_touch_ema50", "EMA50")
    handle_touch(cfg["touch_ema200_d1"], "EMA200", "d1_touch_ema200", "EMA200")

    if cfg["rsi_d1"] and not df_d1.empty:
        r = rsi(df_d1["Close"]).iloc[-1]
        zone = "overbought" if r > 70 else "oversold" if r < 30 else "neutral"
        prev_zone = state.get("d1_rsi_zone", "neutral")
        if zone != prev_zone and zone != "neutral":
            label = "surachat (>70)" if zone == "overbought" else "survente (<30)"
            messages.append(f"RSI D1 = {r:.1f} — entrée en zone de {label} sur {ticker}")
        state["d1_rsi_zone"] = zone

    if cfg["volume_spike_d1"] and not df_d1.empty:
        vol_avg20 = df_d1["Volume"].tail(20).mean()
        vol_jour = df_d1["Volume"].iloc[-1]
        today_str = str(df_d1.index[-1].date())
        spike = bool(vol_avg20 and vol_jour > 1.5 * vol_avg20)
        if spike and state.get("d1_volume_spike_date") != today_str:
            messages.append(f"Volume journalier = {vol_jour / vol_avg20:.2f}x la moyenne 20j sur {ticker}")
            state["d1_volume_spike_date"] = today_str
        elif not spike:
            state["d1_volume_spike_date"] = None

    return messages


def main():
    watchlist = load_watchlist()
    cfg_all = load_alerts_config()
    state_all = load_alerts_state()

    tickers = sorted(set(watchlist) | set(cfg_all.keys()))
    total_sent = 0
    checked = 0

    for ticker in tickers:
        cfg = get_ticker_config(cfg_all, ticker)
        if not any(cfg.values()):
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
