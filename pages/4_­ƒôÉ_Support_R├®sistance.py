import streamlit as st
from utils.data import fetch_data
from utils.charts import plot_chart
from utils.levels import find_pivot_levels

st.set_page_config(page_title="Support / Résistance", page_icon="📐", layout="wide")
st.title("📐 Support / Résistance")

ticker = st.session_state.get("ticker", "NANO.PA")
st.caption(f"Ticker : `{ticker}`")

PERIOD_MAP = {
    "1 jour": ("5d", "5m"),
    "5 jours": ("5d", "15m"),
    "1 mois": ("1mo", "60m"),
    "3 mois": ("3mo", "1d"),
    "6 mois": ("6mo", "1d"),
    "1 an": ("1y", "1d"),
}
period_label = st.selectbox("Période du graphique", list(PERIOD_MAP.keys()), index=1)
period, interval = PERIOD_MAP[period_label]

st.subheader("Affichage des indicateurs")
c1, c2, c3, c4, c5 = st.columns(5)
show_ema8 = c1.checkbox("EMA8", True)
show_ema20 = c2.checkbox("EMA20", True)
show_ema50 = c3.checkbox("EMA50", True)
show_ema200 = c4.checkbox("EMA200", True)
show_vwap = c5.checkbox("VWAP", True)

emas = []
if show_ema8:
    emas.append("EMA8")
if show_ema20:
    emas.append("EMA20")
if show_ema50:
    emas.append("EMA50")
if show_ema200:
    emas.append("EMA200")

df = fetch_data(ticker, period=period, interval=interval)

if df.empty:
    st.warning("Aucune donnée disponible pour ce ticker/période.")
else:
    fig = plot_chart(df, f"{ticker} — {period_label}", show_emas=emas, show_vwap=show_vwap)

    # Niveaux support/résistance calculés sur les 5 derniers jours (bougies 15 min),
    # indépendamment de la période affichée, comme demandé.
    df_5j = fetch_data(ticker, period="5d", interval="15m")
    support, resistance = find_pivot_levels(df_5j, order=3, tolerance_pct=0.5)

    if support:
        fig.add_hline(y=support, line_dash="dash", line_color="#27ae60",
                       annotation_text=f"Support {support:.2f} €", annotation_position="bottom right")
    if resistance:
        fig.add_hline(y=resistance, line_dash="dash", line_color="#c0392b",
                       annotation_text=f"Résistance {resistance:.2f} €", annotation_position="top right")

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Meilleur niveau d'achat (support, 5j)", f"{support:.2f} €" if support else "N/A")
    col2.metric("Meilleur niveau de vente (résistance, 5j)", f"{resistance:.2f} €" if resistance else "N/A")
    st.caption(
        "Niveaux calculés à partir des points pivots (plus hauts / plus bas locaux) "
        "touchés au moins 2 fois sur les 5 derniers jours (bougies 15 min) — c'est-à-dire "
        "des prix qui auraient permis de réaliser le même achat ou la même vente à 2 reprises."
    )
