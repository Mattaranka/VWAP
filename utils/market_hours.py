"""Détermine si on est dans la fenêtre horaire pendant laquelle les alertes automatiques
doivent tourner (pour éviter les vérifications inutiles hors séance)."""
from datetime import datetime, time
from zoneinfo import ZoneInfo

PARIS_TZ = ZoneInfo("Europe/Paris")
MARKET_OPEN = time(8, 30)
MARKET_CLOSE = time(17, 45)


def is_market_hours(now=None) -> bool:
    """Lundi-vendredi, 8h30-17h45 heure de Paris (Europe/Paris, gère automatiquement
    l'heure d'été/hiver)."""
    now = datetime.now(PARIS_TZ) if now is None else now.astimezone(PARIS_TZ)
    if now.weekday() >= 5:  # 5 = samedi, 6 = dimanche
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE
