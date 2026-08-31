"""Suivi de la tendance des grands secteurs européens.

Utilise des ETF sectoriels iShares STOXX Europe 600 comme proxy de chaque secteur — il
n'existe pas d'indice sectoriel "brut" directement et fiablement accessible via Yahoo
Finance, alors que ces ETF sont cotés et suivis. "Santé" couvre l'ensemble du secteur santé
(pharma, dispositifs médicaux, biotech...), pas uniquement la biotech pure.
"""
from utils.data import fetch_data

SECTOR_ETFS = {
    "Santé / Biotech": "EXV4.DE",
    "Banques": "EXV1.DE",
    "Technologie": "EXV3.DE",
    "Pétrole & Gaz": "EXH1.DE",
    "Matières premières": "EXV6.DE",
    "Automobile": "EXV5.DE",
    "Assurance": "EXH5.DE",
    "Télécommunications": "EXV2.DE",
    "Services aux collectivités": "EXH9.DE",
    "Distribution / Retail": "EXH8.DE",
    "Luxe & Biens de consommation": "EXH7.DE",
    "Voyage & Loisirs": "EXV9.DE",
}


def get_sector_performance():
    """Retourne une liste de dicts {nom, ticker, prix, variation_pct} triée par performance
    décroissante. variation_pct = variation du jour (dernière clôture vs clôture précédente)."""
    rows = []
    for name, ticker in SECTOR_ETFS.items():
        df = fetch_data(ticker, period="10d", interval="1d")
        if df.empty or len(df) < 2:
            rows.append({"nom": name, "ticker": ticker, "prix": None, "variation_pct": None})
            continue
        last = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        variation_pct = (last - prev) / prev * 100 if prev else None
        rows.append({"nom": name, "ticker": ticker, "prix": last, "variation_pct": variation_pct})

    rows.sort(key=lambda r: (r["variation_pct"] is None, -(r["variation_pct"] or 0)))
    return rows
