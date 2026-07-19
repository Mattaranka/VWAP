"""Indicateurs techniques : EMA, VWAP, RSI, taille moyenne des bougies."""
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
    cum_tpv = tmp.groupby("_date")["_tpv"].cumsum()
    cum_vol = tmp.groupby("_date")["Volume"].cumsum().replace(0, pd.NA)
    return (cum_tpv / cum_vol).astype(float)


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
