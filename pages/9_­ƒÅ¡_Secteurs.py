import streamlit as st

from utils.sectors import get_sector_performance

st.set_page_config(page_title="Secteurs", page_icon="🏭", layout="wide")
st.title("🏭 Tendance des secteurs (Europe)")

st.caption(
    "Performance du jour de chaque grand secteur européen, basée sur des ETF STOXX Europe 600 "
    "sectoriels (contexte de marché — pas une moyenne de vos propres titres suivis)."
)

with st.spinner("Récupération des données sectorielles..."):
    sectors = get_sector_performance()

cols = st.columns(3)
for i, s in enumerate(sectors):
    col = cols[i % 3]
    if s["variation_pct"] is None:
        col.metric(s["nom"], "N/A")
    else:
        col.metric(s["nom"], f"{s['prix']:.2f} €", delta=f"{s['variation_pct']:+.2f}%")

st.divider()
st.caption(
    "Source : ETF iShares STOXX Europe 600 par secteur (Xetra). Variation = dernière clôture "
    "vs clôture précédente. « Santé / Biotech » couvre l'ensemble du secteur santé "
    "(pharma, dispositifs médicaux, biotech), pas uniquement la biotech pure — c'est la "
    "meilleure approximation disponible."
)
