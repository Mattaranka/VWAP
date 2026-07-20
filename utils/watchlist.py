"""Gestion de la liste des titres suivis (watchlist)."""
import json
import os

WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "..", "watchlist.json")
DEFAULT_WATCHLIST = ["NANO.PA"]


def load_watchlist():
    if os.path.exists(WATCHLIST_PATH):
        try:
            with open(WATCHLIST_PATH) as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    return DEFAULT_WATCHLIST.copy()


def save_watchlist(tickers):
    try:
        with open(WATCHLIST_PATH, "w") as f:
            json.dump(tickers, f, indent=2)
        return True
    except Exception:
        return False
