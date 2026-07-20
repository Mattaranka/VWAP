"""Script autonome (sans Streamlit) pour vérifier les alertes et notifier Telegram.

Destiné à être exécuté périodiquement par GitHub Actions (voir .github/workflows/check_alerts.yml).

Les alertes sont basées sur un CHANGEMENT D'ÉTAT (persisté dans alerts_state.json) plutôt que
sur la comparaison des deux dernières bougies à chaque exécution : cela évite à la fois de
manquer un croisement survenu entre deux vérifications (ex. en M5, où plusieurs bougies
peuvent s'écouler entre deux passages du cron) et d'envoyer la même alerte en boucle tant
que l'état reste inchangé (ex. RSI qui reste au-dessus de 70 pendant plusieurs heures).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data import get_daily, get_h1, get_m5
from utils.indicators import add_emas, rsi
from utils.telegram_utils import send_telegram_message

TICKER = os.environ.get("TICKER", "NANO.PA")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "alerts_config.json")
STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "alerts_state.json")

DEFAULT_CONFIG = {
    "cross_ema_m5": False,
    "cross_ema_h1": False,
    "cross_ema_d1": False,
    "touch_ema20_d1": False,
    "touch_ema50_d1": False,
    "touch_ema200_d1": False,
    "rsi_d1": False,
}

DEFAULT_STATE = {
    "m5_ema_cross": None,
    "h1_ema_cross": None,
    "d1_ema_cross": None,
    "d1_touch_ema20": False,
    "d1_touch_ema50": False,
    "d1_touch_ema200": False,
    "d1_rsi_zone": "neutral",
}


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = default.copy()
                data.update(json.load(f))
                return data
        except Exception:
            return default.copy()
    return default.copy()


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def ema_relation(df):
    """'above' si EMA8 > EMA20, 'below' sinon, None si donnée insuffisante."""
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


def main():
    cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG)
    state = load_json(STATE_PATH, DEFAULT_STATE)
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
            messages.append(f"Croisement EMA8/EMA20 {direction} détecté en {label} sur {TICKER}")
        state[state_key] = rel

    handle_cross(cfg["cross_ema_m5"], get_m5(TICKER, "5d"), "m5_ema_cross", "M5")
    handle_cross(cfg["cross_ema_h1"], get_h1(TICKER, "60d"), "h1_ema_cross", "H1")

    df_d1 = get_daily(TICKER)
    handle_cross(cfg["cross_ema_d1"], df_d1, "d1_ema_cross", "D1")

    def handle_touch(enabled, ema_col, state_key, label):
        if not enabled:
            return
        touching = check_touch(df_d1, ema_col)
        if touching and not state.get(state_key, False):
            messages.append(f"La dernière bougie D1 touche l'{label} sur {TICKER}")
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
            messages.append(f"RSI D1 = {r:.1f} — entrée en zone de {label} sur {TICKER}")
        state["d1_rsi_zone"] = zone

    for m in messages:
        ok, info = send_telegram_message(f"🔔 {m}")
        print(("OK  " if ok else "FAIL"), m, "" if ok else info)

    save_json(STATE_PATH, state)
    print(f"{len(messages)} alerte(s) envoyée(s).")


if __name__ == "__main__":
    main()
