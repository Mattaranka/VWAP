import streamlit as st
from utils.data import get_daily, get_h1, get_h4, get_m5
from utils.charts import plot_chart

st.set_page_config(page_title="Graphiques", page_icon="📊", layout="wide")
st.title("📊 Graphiques multi-timeframes")

ticker = st.session_state.get("ticker", "NANO.PA")
st.caption(f"Ticker : `{ticker}`")

tabs = st.tabs(["Journalier (D1)", "H4", "H1", "M5"])

with tabs[0]:
    df = get_daily(ticker)
    st.plotly_chart(plot_chart(df, f"{ticker} — D1"), use_container_width=True)
    if df.empty:
        st.warning("Aucune donnée disponible pour ce ticker.")

with tabs[1]:
    df = get_h4(ticker)
    st.plotly_chart(plot_chart(df, f"{ticker} — H4 (reconstruit à partir du H1)"), use_container_width=True)
    if df.empty:
        st.warning("Aucune donnée disponible.")

with tabs[2]:
    df = get_h1(ticker)
    st.plotly_chart(plot_chart(df, f"{ticker} — H1"), use_container_width=True)
    if df.empty:
        st.warning("Aucune donnée disponible.")

with tabs[3]:
    df = get_m5(ticker)
    st.plotly_chart(plot_chart(df, f"{ticker} — M5"), use_container_width=True)
    if df.empty:
        st.warning("Aucune donnée disponible.")
