"""Script autonome (sans Streamlit) pour vérifier les alertes et notifier Telegram.
Destiné à être exécuté périodiquement par GitHub Actions (voir .github/workflows/check_alerts.yml),
ce qui permet des notifications même quand l'application Streamlit n'est pas ouverte.
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

DEFAULT_CONFIG = {
    "cross_ema_m5": False,
    "cross_ema_h1": False,
    "cross_ema_d1": False,
    "touch_ema20_d1": False,
    "touch_ema50_d1": False,
    "touch_ema200_d1": False,
    "rsi_d1": False,
}


def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def check_cross(df):
    if df.empty:
        return None
    df = add_emas(df, (8, 20))
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if prev["EMA8"] < prev["EMA20"] and last["EMA8"] >= last["EMA20"]:
        return "haussier"
    if prev["EMA8"] > prev["EMA20"] and last["EMA8"] <= last["EMA20"]:
        return "baissier"
    return None


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
    cfg = load_config()
    messages = []

    if cfg["cross_ema_m5"]:
        c = check_cross(get_m5(TICKER, "5d"))
        if c:
            messages.append(f"Croisement EMA8/EMA20 {c} en M5 sur {TICKER}")
    if cfg["cross_ema_h1"]:
        c = check_cross(get_h1(TICKER, "60d"))
        if c:
            messages.append(f"Croisement EMA8/EMA20 {c} en H1 sur {TICKER}")

    df_d1 = get_daily(TICKER)
    if cfg["cross_ema_d1"]:
        c = check_cross(df_d1)
        if c:
            messages.append(f"Croisement EMA8/EMA20 {c} en D1 sur {TICKER}")
    if cfg["touch_ema20_d1"] and check_touch(df_d1, "EMA20"):
        messages.append(f"Dernière bougie D1 touche l'EMA20 sur {TICKER}")
    if cfg["touch_ema50_d1"] and check_touch(df_d1, "EMA50"):
        messages.append(f"Dernière bougie D1 touche l'EMA50 sur {TICKER}")
    if cfg["touch_ema200_d1"] and check_touch(df_d1, "EMA200"):
        messages.append(f"Dernière bougie D1 touche l'EMA200 sur {TICKER}")
    if cfg["rsi_d1"] and not df_d1.empty:
        r = rsi(df_d1["Close"]).iloc[-1]
        if r > 70:
            messages.append(f"RSI D1 = {r:.1f} (>70, surachat) sur {TICKER}")
        elif r < 30:
            messages.append(f"RSI D1 = {r:.1f} (<30, survente) sur {TICKER}")

    for m in messages:
        ok, info = send_telegram_message(f"🔔 {m}")
        print(("OK  " if ok else "FAIL"), m, "" if ok else info)

    print(f"{len(messages)} alerte(s) envoyée(s).")


if __name__ == "__main__":
    main()
