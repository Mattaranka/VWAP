import streamlit as st

from utils.data import get_h1
from utils.charts import plot_chart_with_rsi
from utils.indicators import rsi
from utils.alerts_store import load_alerts_config, get_ticker_config

st.set_page_config(page_title="H1 + RSI", page_icon="📉", layout="wide")
st.title("📉 Graphique H1 avec RSI")

ticker = st.session_state.get("ticker", "NANO.PA")
st.caption(f"Ticker : `{ticker}`")

df = get_h1(ticker)

if df.empty:
    st.warning("Aucune donnée disponible pour ce ticker.")
else:
    cfg_all = load_alerts_config()
    cfg = get_ticker_config(cfg_all, ticker)
    high_th = int(cfg.get("rsi_h1_high", 67) or 67)
    low_th = int(cfg.get("rsi_h1_low", 33) or 33)

    rsi_series = rsi(df["Close"])
    fig = plot_chart_with_rsi(df, f"{ticker} — H1", rsi_series, thresholds=(high_th, low_th))
    st.plotly_chart(fig, use_container_width=True)

    rsi_val = rsi_series.iloc[-1]
    col1, col2 = st.columns(2)
    col1.metric("RSI H1 actuel", f"{rsi_val:.1f}")
    if rsi_val > high_th:
        col1.caption(f"🔴 Au-dessus du seuil haut ({high_th})")
    elif rsi_val < low_th:
        col1.caption(f"🟢 En-dessous du seuil bas ({low_th})")
    col2.metric("Seuils configurés (alerte RSI H1)", f"Haut {high_th} / Bas {low_th}")
    if not cfg.get("rsi_h1", False):
        col2.caption("ℹ️ L'alerte RSI H1 n'est pas activée pour ce titre (page 🔔 Alertes).")
