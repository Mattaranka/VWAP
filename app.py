import streamlit as st

st.set_page_config(page_title="Nanobiotix Dashboard", page_icon="📈", layout="wide")

if "ticker" not in st.session_state:
    st.session_state["ticker"] = "NANO.PA"

st.sidebar.header("⚙️ Paramètres")
st.session_state["ticker"] = st.sidebar.text_input("Ticker Yahoo Finance", st.session_state["ticker"])
st.sidebar.caption("Ex : `NANO.PA` (Euronext Paris) ou `NBTX` (Nasdaq, ADS)")

st.title("📈 Nanobiotix — Tableau de bord")
st.markdown(
    """
Bienvenue sur le tableau de bord de suivi du titre **Nanobiotix**.

Utilisez le menu à gauche pour naviguer entre les pages :

- **📊 Graphiques** — Journalier, H4, H1, M5 avec EMA 8/20/50/200 et VWAP
- **ℹ️ Info** — volumes, plus haut/bas, RSI, VWAP, taille moyenne des bougies
- **🔔 Alertes** — configuration des notifications Telegram
- **📐 Support / Résistance** — niveaux clés sur différentes périodes
- **🌀 Fibonacci** — retracements sur la période choisie

Le ticker utilisé par toutes les pages est celui défini ci-contre (persistant durant la session).
"""
)

st.info(
    "⚠️ Cet outil est fourni à titre informatif uniquement et ne constitue pas un conseil "
    "en investissement. Les décisions de trading relèvent de votre seule responsabilité."
)
