"""Calculs de synthèse par titre pour la page Watchlist."""
from utils.data import get_daily, fetch_data
from utils.indicators import add_emas, rsi
from utils.levels import find_pivot_levels


def ticker_summary(ticker: str) -> dict:
    df_d1 = get_daily(ticker, period="1y")
    if df_d1.empty or len(df_d1) < 25:
        return {"ticker": ticker, "error": "Pas de données disponibles"}

    df_d1e = add_emas(df_d1, (8, 20, 50, 200))
    last = df_d1e.iloc[-1]
    price = float(last["Close"])
    ema20, ema50 = last["EMA20"], last["EMA50"]

    if ema20 == ema20 and ema50 == ema50:
        if price > ema20 > ema50:
            trend = "Haussière 🟢"
        elif price < ema20 < ema50:
            trend = "Baissière 🔴"
        else:
            trend = "Neutre ⚪"
    else:
        trend = "N/A"

    dist_ema20 = (price - ema20) / ema20 * 100 if ema20 == ema20 and ema20 else float("nan")
    dist_ema50 = (price - ema50) / ema50 * 100 if ema50 == ema50 and ema50 else float("nan")

    rsi_val = float(rsi(df_d1["Close"]).iloc[-1])

    vol_avg20 = df_d1["Volume"].tail(20).mean()
    vol_today = df_d1["Volume"].iloc[-1]
    vol_ratio = float(vol_today / vol_avg20) if vol_avg20 else float("nan")

    df_5j = fetch_data(ticker, period="5d", interval="15m")
    support, resistance = find_pivot_levels(df_5j, order=3, tolerance_pct=0.5)

    return {
        "ticker": ticker,
        "prix": price,
        "tendance": trend,
        "rsi": rsi_val,
        "dist_ema20_pct": dist_ema20,
        "dist_ema50_pct": dist_ema50,
        "vol_ratio": vol_ratio,
        "support": support,
        "resistance": resistance,
    }
