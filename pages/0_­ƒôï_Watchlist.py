import pandas as pd
import streamlit as st

from utils.watchlist import load_watchlist, save_watchlist
from utils.screener import ticker_summary

st.set_page_config(page_title="Watchlist", page_icon="📋", layout="wide")
st.title("📋 Watchlist PEA")

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = load_watchlist()

st.subheader("Gestion de la liste")
c1, c2 = st.columns([3, 1])
new_ticker = c1.text_input("Ajouter un ticker (ex : AI.PA, MC.PA, ALTA.PA...)", "")
if c2.button("➕ Ajouter") and new_ticker.strip():
    t = new_ticker.strip().upper()
    if t not in st.session_state["watchlist"]:
        st.session_state["watchlist"].append(t)
        save_watchlist(st.session_state["watchlist"])
        st.rerun()

to_remove = st.multiselect("Retirer des tickers", st.session_state["watchlist"])
if st.button("🗑️ Retirer la sélection") and to_remove:
    st.session_state["watchlist"] = [t for t in st.session_state["watchlist"] if t not in to_remove]
    save_watchlist(st.session_state["watchlist"])
    st.rerun()

st.caption(
    "⚠️ Cette liste ne vérifie pas automatiquement l'éligibilité PEA — vérifiez chaque titre "
    "auprès de votre courtier avant d'investir."
)

st.divider()
st.subheader("Synthèse du jour")

if not st.session_state["watchlist"]:
    st.info("Ajoutez au moins un ticker pour afficher la synthèse.")
else:
    rows = []
    with st.spinner("Récupération des données..."):
        for t in st.session_state["watchlist"]:
            rows.append(ticker_summary(t))

    display_rows = []
    for r in rows:
        if "error" in r:
            display_rows.append({"Ticker": r["ticker"], "Statut": r["error"]})
            continue
        display_rows.append(
            {
                "Ticker": r["ticker"],
                "Prix": f"{r['prix']:.2f} €",
                "Tendance D1": r["tendance"],
                "RSI D1": f"{r['rsi']:.0f}",
                "Écart EMA20": f"{r['dist_ema20_pct']:+.1f}%",
                "Écart EMA50": f"{r['dist_ema50_pct']:+.1f}%",
                "Volume vs moy.20j": f"{r['vol_ratio']:.2f}x",
                "Support (5j)": f"{r['support']:.2f} €" if r["support"] else "N/A",
                "Résistance (5j)": f"{r['resistance']:.2f} €" if r["resistance"] else "N/A",
            }
        )

    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
    st.caption(
        "Écart EMA : distance du prix par rapport à l'EMA, en %. Support/Résistance calculés "
        "sur les points pivots touchés ≥ 2 fois sur les 5 derniers jours (bougies 15 min)."
    )
