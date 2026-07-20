import streamlit as st
from utils.watchlist import load_watchlist

st.set_page_config(page_title="Dashboard PEA", page_icon="📈", layout="wide")

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = load_watchlist()

if not st.session_state["watchlist"]:
    st.session_state["watchlist"] = ["NANO.PA"]

if "ticker" not in st.session_state or st.session_state["ticker"] not in st.session_state["watchlist"]:
    st.session_state["ticker"] = st.session_state["watchlist"][0]

st.sidebar.header("⚙️ Paramètres")
st.session_state["ticker"] = st.sidebar.selectbox(
    "Titre actif (pages Graphiques / Info / S-R / Fibonacci)",
    st.session_state["watchlist"],
    index=st.session_state["watchlist"].index(st.session_state["ticker"]),
)
st.sidebar.caption("Gérez la liste des titres suivis depuis la page 📋 Watchlist.")

st.title("📈 Tableau de bord PEA — Swing Trading")
st.markdown(
    """
Bienvenue sur votre tableau de bord de suivi multi-titres.

- **📋 Watchlist** — vue d'ensemble de tous vos titres suivis (tendance, RSI, volume, niveaux clés)
- **📊 Graphiques** — Journalier, H4, H1, M5 du titre actif, avec EMA 8/20/50/200 et VWAP
- **ℹ️ Info** — prix actuel, volumes, plus haut/bas, RSI, VWAP, statistiques de bougies du titre actif
- **🔔 Alertes** — configuration des notifications Telegram, par titre
- **📐 Support / Résistance** — niveaux clés sur différentes périodes
- **🌀 Fibonacci** — retracements sur la période choisie

Le titre actif défini ci-contre s'applique aux pages Graphiques, Info, Support/Résistance et
Fibonacci. La Watchlist et les Alertes couvrent, elles, l'ensemble des titres que vous suivez.
"""
)

st.info(
    "⚠️ Cet outil est fourni à titre informatif uniquement et ne constitue pas un conseil "
    "en investissement. Les décisions de trading, ainsi que la vérification de l'éligibilité "
    "PEA de chaque titre, relèvent de votre seule responsabilité."
)
