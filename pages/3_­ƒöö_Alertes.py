import json
import os
import streamlit as st

from utils.data import get_daily, get_h1, get_m5
from utils.indicators import add_emas, rsi
from utils.telegram_utils import send_telegram_message

st.set_page_config(page_title="Alertes", page_icon="🔔", layout="wide")
st.title("🔔 Alertes Telegram")

ticker = st.session_state.get("ticker", "NANO.PA")
st.caption(f"Ticker : `{ticker}`")

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
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False


if "alerts_config" not in st.session_state:
    st.session_state["alerts_config"] = load_config()

cfg = st.session_state["alerts_config"]

st.subheader("Activer / désactiver les alertes")
c1, c2 = st.columns(2)
with c1:
    cfg["cross_ema_m5"] = st.checkbox("Croisement EMA8 / EMA20 — M5", value=cfg["cross_ema_m5"])
    cfg["cross_ema_h1"] = st.checkbox("Croisement EMA8 / EMA20 — H1", value=cfg["cross_ema_h1"])
    cfg["cross_ema_d1"] = st.checkbox("Croisement EMA8 / EMA20 — D1", value=cfg["cross_ema_d1"])
    cfg["rsi_d1"] = st.checkbox("RSI D1 > 70 ou < 30", value=cfg["rsi_d1"])
with c2:
    cfg["touch_ema20_d1"] = st.checkbox("Dernière bougie touche l'EMA20 — D1", value=cfg["touch_ema20_d1"])
    cfg["touch_ema50_d1"] = st.checkbox("Dernière bougie touche l'EMA50 — D1", value=cfg["touch_ema50_d1"])
    cfg["touch_ema200_d1"] = st.checkbox("Dernière bougie touche l'EMA200 — D1", value=cfg["touch_ema200_d1"])

if st.button("💾 Enregistrer la configuration"):
    if save_config(cfg):
        st.success("Configuration enregistrée (utilisée aussi par le script GitHub Actions).")
    else:
        st.error("Impossible d'écrire le fichier de configuration sur cet environnement.")

st.divider()
st.subheader("Test de connexion Telegram")
if st.button("Envoyer un message de test"):
    ok, msg = send_telegram_message(f"✅ Test — Dashboard Nanobiotix connecté ({ticker}).")
    st.success("Message envoyé.") if ok else st.error(f"Échec : {msg}")

st.divider()
st.subheader("Vérification manuelle des alertes")
st.caption(
    "L'application Streamlit ne tourne que lorsque la page est ouverte. Pour un suivi 24/7, "
    "configurez le workflow GitHub Actions fourni (`.github/workflows/check_alerts.yml`), qui "
    "exécute `scripts/check_alerts.py` selon un planning cron indépendant de cette page."
)


def check_cross(df):
    if df.empty:
        return None
    df = add_emas(df, (8, 20))
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if prev["EMA8"] < prev["EMA20"] and last["EMA8"] >= last["EMA20"]:
        return "haussier ↑"
    if prev["EMA8"] > prev["EMA20"] and last["EMA8"] <= last["EMA20"]:
        return "baissier ↓"
    return None


def check_touch(df, ema_col, tol_pct=0.3):
    if df.empty:
        return False
    df = add_emas(df, (8, 20, 50, 200))
    last = df.iloc[-1]
    ema_val = last[ema_col]
    if ema_val != ema_val or ema_val == 0:
        return False
    inside_range = last["Low"] <= ema_val <= last["High"]
    close_enough = abs(last["Close"] - ema_val) / ema_val * 100 <= tol_pct
    return bool(inside_range or close_enough)


if st.button("🔍 Vérifier maintenant"):
    messages = []

    if cfg["cross_ema_m5"]:
        c = check_cross(get_m5(ticker, "5d"))
        if c:
            messages.append(f"Croisement EMA8/EMA20 {c} détecté en M5 sur {ticker}")
    if cfg["cross_ema_h1"]:
        c = check_cross(get_h1(ticker, "60d"))
        if c:
            messages.append(f"Croisement EMA8/EMA20 {c} détecté en H1 sur {ticker}")

    df_d1 = get_daily(ticker)
    if cfg["cross_ema_d1"]:
        c = check_cross(df_d1)
        if c:
            messages.append(f"Croisement EMA8/EMA20 {c} détecté en D1 sur {ticker}")
    if cfg["touch_ema20_d1"] and check_touch(df_d1, "EMA20"):
        messages.append(f"La dernière bougie D1 touche l'EMA20 sur {ticker}")
    if cfg["touch_ema50_d1"] and check_touch(df_d1, "EMA50"):
        messages.append(f"La dernière bougie D1 touche l'EMA50 sur {ticker}")
    if cfg["touch_ema200_d1"] and check_touch(df_d1, "EMA200"):
        messages.append(f"La dernière bougie D1 touche l'EMA200 sur {ticker}")
    if cfg["rsi_d1"] and not df_d1.empty:
        r = rsi(df_d1["Close"]).iloc[-1]
        if r > 70:
            messages.append(f"RSI D1 = {r:.1f} — zone de surachat (>70) sur {ticker}")
        elif r < 30:
            messages.append(f"RSI D1 = {r:.1f} — zone de survente (<30) sur {ticker}")

    if messages:
        for m in messages:
            st.warning(m)
            send_telegram_message(f"🔔 {m}")
        st.success(f"{len(messages)} alerte(s) envoyée(s) sur Telegram.")
    else:
        st.info("Aucune alerte déclenchée pour le moment.")
