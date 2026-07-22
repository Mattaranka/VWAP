"""Récupération des données de marché pour Nanobiotix (via Yahoo Finance)."""
import pandas as pd

try:
    import streamlit as st

    def cache(ttl=60):
        return st.cache_data(ttl=ttl, show_spinner=False)
except Exception:  # pragma: no cover - utilisé hors contexte Streamlit (scripts cron)
    def cache(ttl=60):
        def _wrap(f):
            return f
        return _wrap

import yfinance as yf

DEFAULT_TICKER = "NANO.PA"  # Nanobiotix sur Euronext Paris. Alternative Nasdaq (ADS): "NBTX"


@cache(ttl=60)
def fetch_data(ticker: str = DEFAULT_TICKER, period: str = "60d", interval: str = "5m") -> pd.DataFrame:
    """Télécharge des données OHLCV depuis Yahoo Finance et nettoie le format."""
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.index.tz is not None:
        df.index = df.index.tz_convert("Europe/Paris")
    return df


def resample_h4(df_h1: pd.DataFrame) -> pd.DataFrame:
    """Reconstruit des bougies H4 à partir de données H1 (Yahoo ne fournit pas H4 nativement)."""
    if df_h1.empty:
        return df_h1
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df_h4 = df_h1.resample("4h", origin="start_day").agg(agg).dropna()
    return df_h4


def get_daily(ticker: str = DEFAULT_TICKER, period: str = "2y") -> pd.DataFrame:
    return fetch_data(ticker, period=period, interval="1d")


def get_h1(ticker: str = DEFAULT_TICKER, period: str = "60d") -> pd.DataFrame:
    return fetch_data(ticker, period=period, interval="60m")


def get_h4(ticker: str = DEFAULT_TICKER, period: str = "60d") -> pd.DataFrame:
    df_h1 = get_h1(ticker, period=period)
    return resample_h4(df_h1)


def get_m5(ticker: str = DEFAULT_TICKER, period: str = "5d") -> pd.DataFrame:
    return fetch_data(ticker, period=period, interval="5m")


def get_current_price(ticker: str = DEFAULT_TICKER):
    """Dernier prix connu : dernière clôture intraday (M5) si disponible, sinon dernière
    clôture journalière. Retourne None si aucune donnée n'est disponible."""
    df_m5 = get_m5(ticker, period="5d")
    if not df_m5.empty:
        return float(df_m5["Close"].iloc[-1])
    df_d1 = get_daily(ticker, period="5d")
    if not df_d1.empty:
        return float(df_d1["Close"].iloc[-1])
    return None
