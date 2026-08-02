"""Calculs de performance à partir du journal de trades (avec sorties partielles)."""
from datetime import datetime

import pandas as pd

from utils.data import get_current_price


def sold_quantity(trade):
    return sum(e["quantity"] for e in trade.get("exits", []))


def remaining_quantity(trade):
    return trade["quantity"] - sold_quantity(trade)


def is_open(trade):
    return remaining_quantity(trade) > 0


def exit_pnl(trade, exit_):
    """P&L en € et en % pour une sortie (partielle ou totale) donnée.
    Les frais d'entrée sont alloués au prorata de la quantité vendue."""
    qty = exit_["quantity"]
    entry_fees_alloc = (trade.get("entry_fees", 0) or 0) * qty / trade["quantity"] if trade["quantity"] else 0
    pnl_eur = (exit_["price"] - trade["entry_price"]) * qty - (exit_.get("fees", 0) or 0) - entry_fees_alloc
    entry_value = trade["entry_price"] * qty
    pnl_pct = (pnl_eur / entry_value * 100) if entry_value else 0
    return pnl_eur, pnl_pct


def _leg_type(trade, exit_):
    """'Solde' si cette sortie clôture définitivement la position, sinon 'Partielle'."""
    exits_sorted = sorted(trade.get("exits", []), key=lambda e: e["date"])
    cum = 0
    for e in exits_sorted:
        cum += e["quantity"]
        if e["id"] == exit_["id"]:
            break
    return "Solde" if cum >= trade["quantity"] else "Partielle"


def closed_legs_df(trades):
    """Chaque sortie (partielle ou totale) devient une ligne — c'est l'unité de P&L réalisé."""
    rows = []
    for t in trades:
        for e in t.get("exits", []):
            pnl_eur, pnl_pct = exit_pnl(t, e)
            try:
                entry_d = datetime.fromisoformat(t["entry_date"])
                exit_d = datetime.fromisoformat(e["date"])
                duration = (exit_d - entry_d).days
            except Exception:
                duration = None
            rows.append(
                {
                    "trade_id": t["id"],
                    "exit_id": e["id"],
                    "ticker": t["ticker"],
                    "entry_date": t["entry_date"],
                    "entry_price": t["entry_price"],
                    "exit_date": e["date"],
                    "exit_price": e["price"],
                    "quantity": e["quantity"],
                    "pnl_eur": pnl_eur,
                    "pnl_pct": pnl_pct,
                    "duration_days": duration,
                    "type": _leg_type(t, e),
                    "notes": e.get("notes") or t.get("notes", ""),
                }
            )
    return pd.DataFrame(rows)


def compute_kpis(df_legs):
    """KPIs calculés sur les sorties (chaque vente, partielle ou totale, est un événement
    de P&L réalisé indépendant)."""
    if df_legs.empty:
        return {}
    total_trades = len(df_legs)
    wins = df_legs[df_legs["pnl_eur"] > 0]
    losses = df_legs[df_legs["pnl_eur"] <= 0]
    win_rate = len(wins) / total_trades * 100
    total_pnl = df_legs["pnl_eur"].sum()
    total_invested = (df_legs["entry_price"] * df_legs["quantity"]).sum()
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
    avg_gain = wins["pnl_eur"].mean() if not wins.empty else 0
    avg_loss = losses["pnl_eur"].mean() if not losses.empty else 0
    gross_gain = wins["pnl_eur"].sum()
    gross_loss = abs(losses["pnl_eur"].sum())
    profit_factor = (gross_gain / gross_loss) if gross_loss else (float("inf") if gross_gain else 0)
    best_trade = df_legs["pnl_eur"].max()
    worst_trade = df_legs["pnl_eur"].min()
    avg_duration = df_legs["duration_days"].mean()
    expectancy = df_legs["pnl_eur"].mean()

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "avg_gain": avg_gain,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "avg_duration": avg_duration,
        "expectancy": expectancy,
    }


def open_positions_summary(trades):
    """Une ligne par position encore ouverte (au moins un titre non vendu), sur la base de
    la quantité RESTANTE (après d'éventuelles sorties partielles)."""
    rows = []
    for t in trades:
        remaining = remaining_quantity(t)
        if remaining <= 0:
            continue
        price = get_current_price(t["ticker"])
        entry_value = t["entry_price"] * remaining
        current_value = price * remaining if price is not None else None
        unrealized_pnl = (current_value - entry_value) if current_value is not None else None
        unrealized_pct = (unrealized_pnl / entry_value * 100) if unrealized_pnl is not None and entry_value else None
        rows.append(
            {
                "id": t["id"],
                "ticker": t["ticker"],
                "entry_date": t["entry_date"],
                "entry_price": t["entry_price"],
                "quantity_initial": t["quantity"],
                "quantity_remaining": remaining,
                "quantity_sold": t["quantity"] - remaining,
                "current_price": price,
                "current_value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pct": unrealized_pct,
                "notes": t.get("notes", ""),
            }
        )
    return pd.DataFrame(rows)
