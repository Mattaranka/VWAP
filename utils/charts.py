"""Construction des graphiques chandelier + EMA + VWAP avec Plotly."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def plot_chart_with_rsi(
    df, title, rsi_series, thresholds=(70, 30), show_emas=None, show_vwap=True, extra_periods=(8, 20, 50, 200)
):
    """Graphique chandelier (avec EMA/VWAP) surmontant un sous-graphique RSI, axes X liés."""
    df = df.copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (pas de données)")
        return fig

    df = add_emas(df, extra_periods)
    if show_vwap:
        df["VWAP"] = vwap(df)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, "RSI"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Prix", increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        ),
        row=1,
        col=1,
    )

    emas_to_show = show_emas if show_emas is not None else [f"EMA{p}" for p in extra_periods]
    for e in emas_to_show:
        if e in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df[e], name=e, line=dict(width=1.3, color=EMA_COLORS.get(e))),
                row=1,
                col=1,
            )

    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["VWAP"], name="VWAP", line=dict(width=1.3, dash="dot", color="#16a085")),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Scatter(x=df.index, y=rsi_series, name="RSI", line=dict(width=1.5, color="#8e44ad")),
        row=2,
        col=1,
    )

    high_th, low_th = thresholds
    fig.add_hline(y=high_th, line_dash="dash", line_color="#c0392b", row=2, col=1)
    fig.add_hline(y=low_th, line_dash="dash", line_color="#27ae60", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    fig.update_layout(
        height=750,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig
