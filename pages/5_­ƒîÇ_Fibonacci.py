import streamlit as st
from utils.data import fetch_data
from utils.charts import plot_chart
from utils.levels import fibonacci_levels

st.set_page_config(page_title="Fibonacci", page_icon="🌀", layout="wide")
st.title("🌀 Niveaux de Fibonacci")

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
period_label = st.selectbox("Période", list(PERIOD_MAP.keys()), index=2)
period, interval = PERIOD_MAP[period_label]

df = fetch_data(ticker, period=period, interval=interval)

if df.empty:
    st.warning("Aucune donnée disponible pour ce ticker/période.")
else:
    levels, high, low = fibonacci_levels(df)

    fig = plot_chart(df, f"{ticker} — Fibonacci ({period_label})", show_emas=[], show_vwap=False)
    colors = ["#7f8c8d", "#e67e22", "#8e44ad", "#2980b9", "#27ae60", "#c0392b", "#2c3e50"]
    for (label, val), color in zip(levels.items(), colors):
        fig.add_hline(y=val, line_dash="dot", line_color=color,
                       annotation_text=f"{label} : {val:.2f} €", annotation_position="right")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Niveaux calculés")
    st.table({"Niveau": list(levels.keys()), "Prix": [f"{v:.2f} €" for v in levels.values()]})
    st.caption(f"Retracement calculé entre le plus haut ({high:.2f} €) et le plus bas ({low:.2f} €) de la période.")
