import pandas as pd
import plotly.express as px
import streamlit as st

from utils.journal_store import load_trades
from utils.performance import closed_legs_df, compute_kpis, open_positions_summary, total_fees_paid

st.set_page_config(page_title="Performance", page_icon="📈", layout="wide")
st.title("📈 Dashboard de performance")

trades = load_trades()

if not trades:
    st.info("Ajoutez des trades depuis la page 📒 Journal pour voir vos performances ici.")
    st.stop()

df_legs = closed_legs_df(trades)
kpis = compute_kpis(df_legs) if not df_legs.empty else {}

st.subheader("Indicateurs clés (ventes réalisées, partielles ou totales)")
if not kpis:
    st.info("Aucune vente enregistrée pour le moment — les KPIs apparaîtront après votre première vente.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventes réalisées", kpis["total_trades"])
    c2.metric("Taux de réussite", f"{kpis['win_rate']:.0f}%")
    c3.metric(
        "P&L total réalisé",
        f"{kpis['total_pnl']:+,.2f} €".replace(",", " "),
        delta=f"{kpis['total_pnl_pct']:+.1f}%",
    )
    pf_display = "∞" if kpis["profit_factor"] == float("inf") else f"{kpis['profit_factor']:.2f}"
    c4.metric("Profit factor", pf_display)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Gain moyen", f"{kpis['avg_gain']:+,.2f} €".replace(",", " "))
    c6.metric("Perte moyenne", f"{kpis['avg_loss']:+,.2f} €".replace(",", " "))
    c7.metric("Meilleure vente", f"{kpis['best_trade']:+,.2f} €".replace(",", " "))
    c8.metric("Pire vente", f"{kpis['worst_trade']:+,.2f} €".replace(",", " "))

    c9, c10 = st.columns(2)
    avg_dur = kpis["avg_duration"]
    c9.metric("Durée moyenne de détention", f"{avg_dur:.1f} j" if avg_dur == avg_dur else "N/A")
    c10.metric("Espérance de gain / vente", f"{kpis['expectancy']:+,.2f} €".replace(",", " "))

    st.caption(
        "Chaque vente (partielle ou totale) compte comme un événement de P&L réalisé "
        "indépendant. Alléger une position en 2 fois compte donc pour 2 lignes ci-dessous."
    )

st.metric("💸 Frais totaux payés (entrées + sorties, tout le journal)", f"{total_fees_paid(trades):,.2f} €".replace(",", " "))

st.divider()
st.subheader("💼 Portefeuille actuel")
with st.spinner("Récupération des prix actuels..."):
    df_open = open_positions_summary(trades)

if df_open.empty:
    st.info("Aucune position ouverte actuellement.")
else:
    total_value = df_open["current_value"].dropna().sum()
    total_unreal = df_open["unrealized_pnl"].dropna().sum()
    total_invested_open = (df_open["entry_price"] * df_open["quantity_remaining"]).sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Valeur actuelle", f"{total_value:,.2f} €".replace(",", " "))
    c2.metric("Capital investi (qté restante)", f"{total_invested_open:,.2f} €".replace(",", " "))
    c3.metric("P&L latent", f"{total_unreal:+,.2f} €".replace(",", " "))

st.divider()
st.subheader("Répartitions")

colA, colB = st.columns(2)

with colA:
    st.markdown("**Allocation du portefeuille actuel**")
    if not df_open.empty and df_open["current_value"].notna().any():
        fig_alloc = px.pie(
            df_open.dropna(subset=["current_value"]), names="ticker", values="current_value", hole=0.4
        )
        fig_alloc.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_alloc, use_container_width=True)
    else:
        st.caption("Pas de position ouverte à répartir.")

with colB:
    st.markdown("**Ventes gagnantes vs perdantes**")
    if not df_legs.empty:
        win_loss = pd.DataFrame(
            {
                "Résultat": ["Gagnantes", "Perdantes"],
                "Nombre": [
                    int((df_legs["pnl_eur"] > 0).sum()),
                    int((df_legs["pnl_eur"] <= 0).sum()),
                ],
            }
        )
        fig_wl = px.pie(
            win_loss,
            names="Résultat",
            values="Nombre",
            hole=0.4,
            color="Résultat",
            color_discrete_map={"Gagnantes": "#26a69a", "Perdantes": "#ef5350"},
        )
        fig_wl.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_wl, use_container_width=True)
    else:
        st.caption("Pas encore de vente enregistrée.")

st.markdown("**P&L cumulé par titre (ventes réalisées)**")
if not df_legs.empty:
    by_ticker = df_legs.groupby("ticker")["pnl_eur"].sum().reset_index().sort_values("pnl_eur")
    fig_bar = px.bar(
        by_ticker,
        x="pnl_eur",
        y="ticker",
        orientation="h",
        color=by_ticker["pnl_eur"] > 0,
        color_discrete_map={True: "#26a69a", False: "#ef5350"},
    )
    fig_bar.update_layout(
        height=max(300, 40 * len(by_ticker)),
        showlegend=False,
        xaxis_title="P&L (€)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.caption("Pas encore de vente enregistrée.")

st.divider()
st.subheader("Courbe de performance (P&L cumulé réalisé)")
if not df_legs.empty:
    df_sorted = df_legs.sort_values("exit_date").copy()
    df_sorted["pnl_cumule"] = df_sorted["pnl_eur"].cumsum()
    fig_curve = px.line(df_sorted, x="exit_date", y="pnl_cumule", markers=True)
    fig_curve.update_layout(
        height=420,
        xaxis_title="Date de vente",
        yaxis_title="P&L cumulé (€)",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig_curve.add_hline(y=0, line_dash="dot", line_color="gray")
    st.plotly_chart(fig_curve, use_container_width=True)
else:
    st.caption("La courbe apparaîtra après votre première vente.")
