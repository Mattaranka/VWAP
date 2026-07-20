import json

import streamlit as st

from utils.watchlist import load_watchlist
from utils.data import get_daily, get_h1, get_m5
from utils.indicators import add_emas, rsi
from utils.telegram_utils import send_telegram_message
from utils.github_sync import push_file, is_configured
from utils.alerts_store import (
    load_alerts_config,
    save_alerts_config,
    get_ticker_config,
)

st.set_page_config(page_title="Alertes", page_icon="🔔", layout="wide")
st.title("🔔 Alertes Telegram")

watchlist = load_watchlist()
if not watchlist:
    st.warning("Ajoutez au moins un titre depuis la page 📋 Watchlist avant de configurer des alertes.")
    st.stop()

default_ticker = st.session_state.get("ticker", watchlist[0])
default_index = watchlist.index(default_ticker) if default_ticker in watchlist else 0
ticker = st.selectbox("Titre à configurer", watchlist, index=default_index)

cfg_all = load_alerts_config()
cfg = get_ticker_config(cfg_all, ticker)

st.subheader(f"Activer / désactiver les alertes — {ticker}")
c1, c2 = st.columns(2)
with c1:
    cfg["cross_ema_m5"] = st.checkbox("Croisement EMA8 / EMA20 — M5", value=cfg["cross_ema_m5"], key=f"m5_{ticker}")
    cfg["cross_ema_h1"] = st.checkbox("Croisement EMA8 / EMA20 — H1", value=cfg["cross_ema_h1"], key=f"h1_{ticker}")
    cfg["cross_ema_d1"] = st.checkbox("Croisement EMA8 / EMA20 — D1", value=cfg["cross_ema_d1"], key=f"d1_{ticker}")
    cfg["rsi_d1"] = st.checkbox("RSI D1 > 70 ou < 30", value=cfg["rsi_d1"], key=f"rsi_{ticker}")
with c2:
    cfg["touch_ema20_d1"] = st.checkbox(
        "Dernière bougie touche l'EMA20 — D1", value=cfg["touch_ema20_d1"], key=f"t20_{ticker}"
    )
    cfg["touch_ema50_d1"] = st.checkbox(
        "Dernière bougie touche l'EMA50 — D1", value=cfg["touch_ema50_d1"], key=f"t50_{ticker}"
    )
    cfg["touch_ema200_d1"] = st.checkbox(
        "Dernière bougie touche l'EMA200 — D1", value=cfg["touch_ema200_d1"], key=f"t200_{ticker}"
    )
    cfg["volume_spike_d1"] = st.checkbox(
        "Volume journalier > 1.5x volume moyen (20j)", value=cfg["volume_spike_d1"], key=f"vol_{ticker}"
    )

if st.button("💾 Enregistrer la configuration"):
    cfg_all[ticker] = cfg
    if save_alerts_config(cfg_all):
        st.success(f"Configuration enregistrée pour {ticker}.")
        if is_configured():
            ok, msg = push_file(
                "alerts_config.json",
                json.dumps(cfg_all, indent=2, ensure_ascii=False),
                f"Update alerts config for {ticker} via app",
            )
            if ok:
                st.toast("Configuration synchronisée sur GitHub ✅")
            else:
                st.warning(f"Enregistré localement, mais échec de synchro GitHub : {msg}")
        else:
            st.caption(
                "ℹ️ Synchronisation GitHub non configurée : le workflow GitHub Actions ne verra "
                "ce changement qu'après un committ manuel du fichier (voir README)."
            )
    else:
        st.error("Impossible d'écrire le fichier de configuration sur cet environnement.")

st.divider()
st.subheader("Récapitulatif de la watchlist")
for t in watchlist:
    c = get_ticker_config(cfg_all, t)
    active = [k for k, v in c.items() if v]
    st.write(f"**{t}** — {', '.join(active) if active else 'aucune alerte active'}")

st.divider()
st.subheader("Test de connexion Telegram")
if st.button("Envoyer un message de test"):
    ok, msg = send_telegram_message(f"✅ Test — Dashboard PEA connecté ({ticker}).")
    st.success("Message envoyé.") if ok else st.error(f"Échec : {msg}")

st.divider()
st.subheader(f"Vérification manuelle des alertes — {ticker}")
st.caption(
    "Pour un suivi 24/7 sur l'ensemble de la watchlist, le workflow GitHub Actions fourni "
    "(`.github/workflows/check_alerts.yml`) exécute `scripts/check_alerts.py` en boucle sur "
    "tous les titres, indépendamment de cette page."
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
    return bool(last["Low"] <= ema_val <= last["High"] or abs(last["Close"] - ema_val) / ema_val * 100 <= tol_pct)


if st.button("🔍 Vérifier maintenant (ce titre uniquement)"):
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
    if cfg["volume_spike_d1"] and not df_d1.empty:
        vol_avg20 = df_d1["Volume"].tail(20).mean()
        vol_jour = df_d1["Volume"].iloc[-1]
        if vol_avg20 and vol_jour > 1.5 * vol_avg20:
            messages.append(f"Volume journalier = {vol_jour / vol_avg20:.2f}x la moyenne 20j sur {ticker}")

    if messages:
        for m in messages:
            st.warning(m)
            send_telegram_message(f"🔔 {m}")
        st.success(f"{len(messages)} alerte(s) envoyée(s) sur Telegram.")
    else:
        st.info("Aucune alerte déclenchée pour le moment.")
