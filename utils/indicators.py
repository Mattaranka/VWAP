"""Indicateurs techniques : EMA, VWAP, RSI, taille moyenne des bougies."""
import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def add_emas(df: pd.DataFrame, periods=(8, 20, 50, 200)) -> pd.DataFrame:
    df = df.copy()
    for p in periods:
        df[f"EMA{p}"] = ema(df["Close"], p)
    return df


def vwap(df: pd.DataFrame) -> pd.Series:
    """VWAP intraday, remis à zéro chaque jour (basé sur le prix typique)."""
    if df.empty:
        return pd.Series(dtype=float)
    tmp = df.copy()
    tmp["_date"] = tmp.index.date
    typical_price = (tmp["High"] + tmp["Low"] + tmp["Close"]) / 3
    tmp["_tpv"] = typical_price * tmp["Volume"]
    cum_tpv = tmp.groupby("_date")["_tpv"].cumsum().astype(float)
    cum_vol = tmp.groupby("_date")["Volume"].cumsum().astype(float)
    cum_vol = cum_vol.where(cum_vol != 0, np.nan)
    return cum_tpv / cum_vol


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def avg_candle_size(df: pd.DataFrame, period: int = 14) -> float:
    """Moyenne de la taille (High - Low) des N dernières bougies. Ce n'est PAS l'ATR
    (pas de prise en compte des gaps via le close précédent)."""
    if df.empty:
        return float("nan")
    size = df["High"] - df["Low"]
    return float(size.tail(period).mean())


def wick_stats(df: pd.DataFrame, period: int = 14):
    """Sur les N dernières bougies, calcule :
    - la taille moyenne (Haut - Bas) en % du prix d'ouverture
    - la hausse moyenne (Haut - Ouverture) en % du prix d'ouverture
    - la baisse moyenne (Ouverture - Bas) en % du prix d'ouverture
    Retourne (taille_pct, hausse_pct, baisse_pct)."""
    if df.empty:
        return float("nan"), float("nan"), float("nan")
    d = df.tail(period)
    size_pct = ((d["High"] - d["Low"]) / d["Open"] * 100).mean()
    up_pct = ((d["High"] - d["Open"]) / d["Open"] * 100).mean()
    down_pct = ((d["Open"] - d["Low"]) / d["Open"] * 100).mean()
    return float(size_pct), float(up_pct), float(down_pct)
