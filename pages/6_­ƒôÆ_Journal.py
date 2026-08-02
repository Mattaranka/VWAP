import json
from datetime import date

import pandas as pd
import streamlit as st

from utils.watchlist import load_watchlist
from utils.journal_store import load_trades, save_trades, new_id
from utils.performance import closed_legs_df, open_positions_summary, remaining_quantity
from utils.github_sync import push_file, is_configured

st.set_page_config(page_title="Journal de trades", page_icon="📒", layout="wide")
st.title("📒 Journal de trades & Portefeuille")

watchlist = load_watchlist()

if "trades" not in st.session_state:
    st.session_state["trades"] = load_trades()


def persist_trades():
    save_trades(st.session_state["trades"])
    if is_configured():
        ok, msg = push_file(
            "trades_journal.json",
            json.dumps(st.session_state["trades"], indent=2, ensure_ascii=False),
            "Update trades journal via app",
        )
        if ok:
            st.toast("Journal synchronisé sur GitHub ✅")
        else:
            st.warning(f"Enregistré localement, mais échec de synchro GitHub : {msg}")


st.subheader("➕ Ouvrir une nouvelle position")
with st.form("add_trade_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    ticker_choice = c1.selectbox("Titre (watchlist)", watchlist if watchlist else ["NANO.PA"])
    ticker_manual = c1.text_input("...ou un autre ticker", "")
    entry_date = c2.date_input("Date d'entrée", value=date.today())
    entry_price = c2.number_input("Prix d'entrée (€)", min_value=0.0, step=0.01, format="%.2f")
    quantity = c3.number_input("Quantité", min_value=0, step=1)
    entry_fees = c3.number_input("Frais d'entrée (€)", min_value=0.0, step=0.01, format="%.2f", value=0.0)
    notes = st.text_area("Notes (stratégie, raison d'entrée...)", "")
    submitted = st.form_submit_button("Ouvrir la position")
    if submitted:
        t = ticker_manual.strip().upper() if ticker_manual.strip() else ticker_choice
        if not t or entry_price <= 0 or quantity <= 0:
            st.error("Merci de renseigner au minimum le titre, le prix d'entrée et la quantité.")
        else:
            st.session_state["trades"].append(
                {
                    "id": new_id(),
                    "ticker": t,
                    "entry_date": str(entry_date),
                    "entry_price": entry_price,
                    "quantity": int(quantity),
                    "entry_fees": entry_fees,
                    "notes": notes,
                    "exits": [],
                }
            )
            persist_trades()
            st.success(f"Position ouverte sur {t}.")
            st.rerun()

st.divider()
st.subheader("💼 Portefeuille actuel (positions ouvertes)")

open_trades = [t for t in st.session_state["trades"] if remaining_quantity(t) > 0]
if not open_trades:
    st.info("Aucune position ouverte.")
else:
    with st.spinner("Récupération des prix actuels..."):
        df_open = open_positions_summary(st.session_state["trades"])

    display_show = pd.DataFrame(
        {
            "Titre": df_open["ticker"],
            "Entrée": df_open["entry_date"],
            "Prix entrée": df_open["entry_price"].map(lambda x: f"{x:.2f} €"),
            "Qté restante": df_open["quantity_remaining"],
            "Qté déjà vendue": df_open["quantity_sold"],
            "Prix actuel": df_open["current_price"].map(
                lambda x: f"{x:.2f} €" if x == x and x is not None else "N/A"
            ),
            "Valeur actuelle": df_open["current_value"].map(
                lambda x: f"{x:.2f} €" if x is not None else "N/A"
            ),
            "P&L latent": df_open["unrealized_pnl"].map(
                lambda x: f"{x:+.2f} €" if x is not None else "N/A"
            ),
            "P&L latent %": df_open["unrealized_pct"].map(
                lambda x: f"{x:+.1f}%" if x is not None else "N/A"
            ),
        }
    )
    st.dataframe(display_show, use_container_width=True, hide_index=True)

    total_invested = (df_open["entry_price"] * df_open["quantity_remaining"]).sum()
    total_value = df_open["current_value"].dropna().sum()
    total_unreal = df_open["unrealized_pnl"].dropna().sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Capital investi (positions ouvertes)", f"{total_invested:,.2f} €".replace(",", " "))
    c2.metric("Valeur actuelle du portefeuille", f"{total_value:,.2f} €".replace(",", " "))
    c3.metric("P&L latent total", f"{total_unreal:+,.2f} €".replace(",", " "))

    st.markdown("##### 📤 Alléger ou clôturer une position")
    ids = {
        f"{t['ticker']} — entrée {t['entry_date']} @ {t['entry_price']:.2f}€ "
        f"— reste {remaining_quantity(t)}/{t['quantity']}": t["id"]
        for t in open_trades
    }
    choice = st.selectbox("Position concernée", list(ids.keys()))
    selected_id = ids[choice]
    selected_trade = next(t for t in st.session_state["trades"] if t["id"] == selected_id)
    remaining = remaining_quantity(selected_trade)

    cc1, cc2, cc3, cc4 = st.columns(4)
    sale_date = cc1.date_input("Date de vente", value=date.today(), key="sale_date_input")
    sale_price = cc2.number_input("Prix de vente (€)", min_value=0.0, step=0.01, format="%.2f", key="sale_price_input")
    sale_qty = cc3.number_input(
        "Quantité vendue", min_value=1, max_value=int(remaining), value=int(remaining), step=1, key="sale_qty_input"
    )
    sale_fees = cc4.number_input("Frais (€)", min_value=0.0, step=0.01, format="%.2f", value=0.0, key="sale_fees_input")
    sale_notes = st.text_input("Notes sur cette vente (optionnel)", "", key="sale_notes_input")

    st.caption(
        f"Il reste {remaining} titre(s) sur cette position. Laissez la quantité au maximum "
        "pour clôturer entièrement, ou réduisez-la pour alléger progressivement."
    )

    if st.button("✅ Enregistrer cette vente"):
        if sale_price <= 0:
            st.error("Merci de renseigner un prix de vente.")
        elif sale_qty > remaining:
            st.error(f"La quantité vendue ne peut pas dépasser la quantité restante ({remaining}).")
        else:
            for t in st.session_state["trades"]:
                if t["id"] == selected_id:
                    t.setdefault("exits", []).append(
                        {
                            "id": new_id(),
                            "date": str(sale_date),
                            "price": sale_price,
                            "quantity": int(sale_qty),
                            "fees": sale_fees,
                            "notes": sale_notes,
                        }
                    )
                    break
            persist_trades()
            reste = remaining - sale_qty
            if reste == 0:
                st.success("Position clôturée intégralement.")
            else:
                st.success(f"Vente partielle enregistrée — il reste {reste} titre(s) sur cette position.")
            st.rerun()

st.divider()
st.subheader("📜 Historique des ventes (partielles et totales)")

df_legs = closed_legs_df(st.session_state["trades"])
if df_legs.empty:
    st.info("Aucune vente enregistrée pour le moment.")
else:
    display_closed = pd.DataFrame(
        {
            "Titre": df_legs["ticker"],
            "Entrée": df_legs["entry_date"],
            "Vente": df_legs["exit_date"],
            "Type": df_legs["type"],
            "Prix entrée": df_legs["entry_price"].map(lambda x: f"{x:.2f} €"),
            "Prix vente": df_legs["exit_price"].map(lambda x: f"{x:.2f} €"),
            "Quantité": df_legs["quantity"],
            "Durée (j)": df_legs["duration_days"],
            "P&L": df_legs["pnl_eur"].map(lambda x: f"{x:+.2f} €"),
            "P&L %": df_legs["pnl_pct"].map(lambda x: f"{x:+.1f}%"),
            "Notes": df_legs["notes"],
        }
    ).sort_values("Vente", ascending=False)
    st.dataframe(display_closed, use_container_width=True, hide_index=True)

st.divider()
with st.expander("🗑️ Corrections"):
    st.markdown("**Supprimer une position entière (y compris toutes ses ventes)**")
    if st.session_state["trades"]:
        labels = {
            f"{t['ticker']} — {t['entry_date']} @ {t['entry_price']:.2f}€ x{t['quantity']}"
            f" ({'ouverte' if remaining_quantity(t) > 0 else 'clôturée'})": t["id"]
            for t in st.session_state["trades"]
        }
        to_delete = st.selectbox("Position à supprimer", list(labels.keys()), key="delete_trade_select")
        if st.button("Supprimer cette position"):
            trade_id = labels[to_delete]
            st.session_state["trades"] = [t for t in st.session_state["trades"] if t["id"] != trade_id]
            persist_trades()
            st.success("Position supprimée.")
            st.rerun()
    else:
        st.caption("Aucune position enregistrée.")

    st.markdown("**Annuler une vente précise (partielle ou totale)**")
    exit_labels = {}
    for t in st.session_state["trades"]:
        for e in t.get("exits", []):
            key = f"{t['ticker']} — vente du {e['date']} : {e['quantity']} @ {e['price']:.2f}€"
            exit_labels[key] = (t["id"], e["id"])
    if exit_labels:
        to_undo = st.selectbox("Vente à annuler", list(exit_labels.keys()), key="undo_exit_select")
        if st.button("Annuler cette vente"):
            trade_id, exit_id = exit_labels[to_undo]
            for t in st.session_state["trades"]:
                if t["id"] == trade_id:
                    t["exits"] = [e for e in t.get("exits", []) if e["id"] != exit_id]
                    break
            persist_trades()
            st.success("Vente annulée, la quantité correspondante redevient disponible.")
            st.rerun()
    else:
        st.caption("Aucune vente enregistrée.")
