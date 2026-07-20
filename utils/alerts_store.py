"""Gestion partagée de la configuration et de l'état des alertes, par titre.

Structure de alerts_config.json et alerts_state.json : un objet dont chaque clé est un
ticker, associé à son propre dictionnaire de réglages / état.
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "alerts_config.json")
STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "alerts_state.json")

DEFAULT_TICKER_CONFIG = {
    "cross_ema_m5": False,
    "cross_ema_h1": False,
    "cross_ema_d1": False,
    "touch_ema20_d1": False,
    "touch_ema50_d1": False,
    "touch_ema200_d1": False,
    "rsi_d1": False,
    "volume_spike_d1": False,
}

DEFAULT_TICKER_STATE = {
    "m5_ema_cross": None,
    "h1_ema_cross": None,
    "d1_ema_cross": None,
    "d1_touch_ema20": False,
    "d1_touch_ema50": False,
    "d1_touch_ema200": False,
    "d1_rsi_zone": "neutral",
    "d1_volume_spike_date": None,
}


def _load(path):
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _save(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_alerts_config():
    return _load(CONFIG_PATH)


def save_alerts_config(cfg):
    return _save(CONFIG_PATH, cfg)


def load_alerts_state():
    return _load(STATE_PATH)


def save_alerts_state(state):
    return _save(STATE_PATH, state)


def get_ticker_config(cfg, ticker):
    merged = DEFAULT_TICKER_CONFIG.copy()
    merged.update(cfg.get(ticker, {}))
    return merged


def get_ticker_state(state, ticker):
    merged = DEFAULT_TICKER_STATE.copy()
    merged.update(state.get(ticker, {}))
    return merged
