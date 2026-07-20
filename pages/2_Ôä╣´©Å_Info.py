import streamlit as st
from utils.data import get_daily, get_m5
from utils.indicators import rsi, avg_candle_size, wick_stats, vwap

st.set_page_config(page_title="Info", page_icon="ℹ️", layout="wide")
st.title("ℹ️ Informations clés")

ticker = st.session_state.get("ticker", "NANO.PA")
st.caption(f"Ticker : `{ticker}`")

df = get_daily(ticker, period="2y")
df_m5 = get_m5(ticker, period="5d")

if df.empty:
    st.warning("Aucune donnée disponible pour ce ticker.")
else:
    # Prix actuel : dernier prix intraday si disponible (marché ouvert), sinon dernière clôture
    if not df_m5.empty:
        prix_actuel = float(df_m5["Close"].iloc[-1])
    else:
        prix_actuel = float(df["Close"].iloc[-1])

    vol_moy_20 = df["Volume"].tail(20).mean()
    vol_jour = df["Volume"].iloc[-1]
    high_52 = df["High"].tail(252).max()
    low_52 = df["Low"].tail(252).min()
    high_5 = df["High"].tail(5).max()
    low_5 = df["Low"].tail(5).min()

    taille_moy_eur = avg_candle_size(df, 14)
    taille_moy_pct, hausse_moy_pct, baisse_moy_pct = wick_stats(df, 14)

    rsi_series = rsi(df["Close"])
    rsi_d1 = rsi_series.iloc[-1]

    vwap_val = float("nan")
    if not df_m5.empty:
        vwap_series = vwap(df_m5)
        today = df_m5.index[-1].date()
        vwap_today = vwap_series[df_m5.index.date == today]
        if len(vwap_today):
            vwap_val = vwap_today.iloc[-1]

    st.metric("💰 Prix actuel", f"{prix_actuel:.2f} €")

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Volume moyen (20 derniers jours)", f"{vol_moy_20:,.0f}".replace(",", " "))
    col1.metric("Volume du jour", f"{vol_jour:,.0f}".replace(",", " "))
    if vol_moy_20:
        col1.caption(f"soit {vol_jour / vol_moy_20:.2f}x la moyenne 20j")
    col2.metric("Plus haut 52 semaines", f"{high_52:.2f} €")
    col2.metric("Plus bas 52 semaines", f"{low_52:.2f} €")
    col3.metric("Plus haut 5 jours", f"{high_5:.2f} €")
    col3.metric("Plus bas 5 jours", f"{low_5:.2f} €")

    st.divider()

    col4, col5, col6 = st.columns(3)
    col4.metric("Taille moy. des bougies (14j)", f"{taille_moy_eur:.3f} €")
    col4.caption(f"soit {taille_moy_pct:.2f}% du prix d'ouverture — n'est pas l'ATR")
    col5.metric("Hausse moy. — mèche haute (14j)", f"{hausse_moy_pct:.2f}%")
    col5.caption("Moyenne de (Haut − Ouverture) / Ouverture")
    col6.metric("Baisse moy. — mèche basse (14j)", f"{baisse_moy_pct:.2f}%")
    col6.caption("Moyenne de (Ouverture − Bas) / Ouverture")

    st.divider()

    col7, col8 = st.columns(2)
    col7.metric("RSI journalier (14)", f"{rsi_d1:.1f}")
    if rsi_d1 > 70:
        col7.caption("🔴 Zone de surachat")
    elif rsi_d1 < 30:
        col7.caption("🟢 Zone de survente")
    col8.metric("VWAP (session en cours)", f"{vwap_val:.2f} €" if vwap_val == vwap_val else "N/A")
