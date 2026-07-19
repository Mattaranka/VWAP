"""Construction des graphiques chandelier + EMA + VWAP avec Plotly."""
import plotly.graph_objects as go
from utils.indicators import add_emas, vwap

EMA_COLORS = {"EMA8": "#f39c12", "EMA20": "#2980b9", "EMA50": "#8e44ad", "EMA200": "#2c3e50"}


def plot_chart(df, title, show_emas=None, show_vwap=True, extra_periods=(8, 20, 50, 200)):
    df = df.copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (pas de données)")
        return fig

    df = add_emas(df, extra_periods)
    if show_vwap:
        df["VWAP"] = vwap(df)

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Prix", increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        )
    )

    emas_to_show = show_emas if show_emas is not None else [f"EMA{p}" for p in extra_periods]
    for e in emas_to_show:
        if e in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[e], name=e, line=dict(width=1.3, color=EMA_COLORS.get(e))))

    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["VWAP"], name="VWAP", line=dict(width=1.3, dash="dot", color="#16a085"))
        )

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig
