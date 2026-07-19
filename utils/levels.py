"""Détection de niveaux de support / résistance et calcul des retracements Fibonacci."""


def find_pivot_levels(df, order: int = 3, tolerance_pct: float = 0.5):
    """Détecte les points pivots (plus hauts/plus bas locaux) et regroupe ceux qui
    sont proches en niveaux. Ne retient que les niveaux touchés au moins 2 fois
    (= le niveau aurait permis 2 achats ou 2 ventes identiques sur la période)."""
    if df.empty or len(df) < (2 * order + 1):
        return None, None

    highs = df["High"].values
    lows = df["Low"].values
    n = len(df)

    pivot_highs, pivot_lows = [], []
    for i in range(order, n - order):
        window_h = highs[i - order : i + order + 1]
        window_l = lows[i - order : i + order + 1]
        if highs[i] == window_h.max():
            pivot_highs.append(float(highs[i]))
        if lows[i] == window_l.min():
            pivot_lows.append(float(lows[i]))

    def cluster(vals, tol_pct):
        clusters = []
        for v in sorted(vals):
            placed = False
            for c in clusters:
                if c["mean"] != 0 and abs(v - c["mean"]) / c["mean"] * 100 <= tol_pct:
                    c["points"].append(v)
                    c["mean"] = sum(c["points"]) / len(c["points"])
                    placed = True
                    break
            if not placed:
                clusters.append({"mean": v, "points": [v]})
        return [c for c in clusters if len(c["points"]) >= 2]

    res_clusters = cluster(pivot_highs, tolerance_pct)
    sup_clusters = cluster(pivot_lows, tolerance_pct)

    resistance = max(res_clusters, key=lambda c: c["mean"])["mean"] if res_clusters else (
        max(pivot_highs) if pivot_highs else None
    )
    support = min(sup_clusters, key=lambda c: c["mean"])["mean"] if sup_clusters else (
        min(pivot_lows) if pivot_lows else None
    )
    return support, resistance


def fibonacci_levels(df):
    """Calcule les niveaux de Fibonacci entre le plus haut et le plus bas de la période."""
    high = float(df["High"].max())
    low = float(df["Low"].min())
    diff = high - low
    ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    levels = {f"{r * 100:.1f}%": high - diff * r for r in ratios}
    return levels, high, low
