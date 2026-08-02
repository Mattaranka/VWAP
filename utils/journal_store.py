"""Gestion du journal de trades (positions ouvertes, allégées progressivement ou clôturées).

Format d'un trade (position) :
{
    "id": "...",
    "ticker": "NANO.PA",
    "entry_date": "2026-06-01",
    "entry_price": 5.0,
    "quantity": 1000,          # quantité initiale achetée
    "entry_fees": 2.0,         # frais payés à l'achat
    "notes": "...",
    "exits": [                 # une ou plusieurs sorties partielles (ou une seule totale)
        {"id": "...", "date": "2026-06-10", "price": 5.75, "quantity": 400, "fees": 1.0, "notes": "..."},
        ...
    ]
}

La quantité restante (position encore ouverte) = quantity - somme des quantités déjà vendues.
Une position est "ouverte" tant qu'il reste des titres non vendus.
"""
import json
import os
import uuid

TRADES_PATH = os.path.join(os.path.dirname(__file__), "..", "trades_journal.json")


def new_id():
    return uuid.uuid4().hex[:12]


def _migrate_trade(t):
    """Compatibilité ascendante : convertit un trade de l'ancien format (une seule sortie,
    champs exit_date/exit_price/fees) vers le nouveau format à sorties multiples."""
    if "exits" in t:
        t.setdefault("entry_fees", t.get("fees", 0) or 0)
        t.setdefault("notes", "")
        for e in t["exits"]:
            e.setdefault("id", new_id())
            e.setdefault("fees", 0)
            e.setdefault("notes", "")
        return t

    migrated = {
        "id": t.get("id", new_id()),
        "ticker": t["ticker"],
        "entry_date": t["entry_date"],
        "entry_price": t["entry_price"],
        "quantity": t["quantity"],
        "entry_fees": 0,
        "notes": t.get("notes", ""),
        "exits": [],
    }
    if t.get("exit_price"):
        migrated["exits"].append(
            {
                "id": new_id(),
                "date": t["exit_date"],
                "price": t["exit_price"],
                "quantity": t["quantity"],
                "fees": t.get("fees", 0) or 0,
                "notes": "",
            }
        )
    else:
        migrated["entry_fees"] = t.get("fees", 0) or 0
    return migrated


def load_trades():
    if os.path.exists(TRADES_PATH):
        try:
            with open(TRADES_PATH) as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [_migrate_trade(t) for t in data]
        except Exception:
            return []
    return []


def save_trades(trades):
    try:
        with open(TRADES_PATH, "w") as f:
            json.dump(trades, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
