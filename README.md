# 📈 Nanobiotix Dashboard

Application Streamlit de suivi en temps réel du titre **Nanobiotix** (Euronext Paris : `NANO.PA`,
ou Nasdaq ADS : `NBTX`), avec graphiques multi-timeframes, indicateurs clés, alertes Telegram,
support/résistance et niveaux de Fibonacci.

## Fonctionnalités

- **📊 Graphiques** : D1, H4 (reconstruit à partir du H1), H1, M5 — EMA 8/20/50/200 + VWAP
- **ℹ️ Info** : volume moyen 20j, volume du jour, plus haut/bas 52 semaines et 5 jours,
  taille moyenne des bougies sur 14 jours, RSI journalier, VWAP de la session en cours
- **🔔 Alertes** : notifications Telegram activables/désactivables (croisements EMA8/EMA20 en
  M5/H1/D1, contact avec EMA20/50/200 en D1, RSI D1 hors zone 30-70)
- **📐 Support / Résistance** : graphique multi-périodes (1j à 1an), EMA et VWAP affichables/masquables,
  niveaux d'achat/vente issus des points pivots touchés au moins 2 fois sur 5 jours
- **🌀 Fibonacci** : retracements sur la période sélectionnée

## Installation locale

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # puis renseignez vos clés Telegram
streamlit run app.py
```

## Configuration Telegram

1. Créez un bot via [@BotFather](https://t.me/BotFather) sur Telegram → récupérez le `bot_token`.
2. Envoyez un message à votre bot, puis récupérez votre `chat_id` via
   `https://api.telegram.org/bot<TOKEN>/getUpdates`.
3. Renseignez ces valeurs dans `.streamlit/secrets.toml` (local) ou dans les **Secrets** de
   Streamlit Community Cloud (déploiement).

## Déploiement sur Streamlit Community Cloud

1. Poussez ce dépôt sur GitHub.
2. Sur [share.streamlit.io](https://share.streamlit.io), créez une nouvelle app pointant vers
   `app.py`.
3. Ajoutez `telegram.bot_token` et `telegram.chat_id` dans les Secrets de l'app.

⚠️ Une app Streamlit Cloud se met en veille sans activité et ne peut donc pas garantir des
alertes 24/7. Pour un suivi continu même app fermée, utilisez le workflow GitHub Actions ci-dessous.

## Alertes automatiques via GitHub Actions (recommandé)

Le fichier `.github/workflows/check_alerts.yml` exécute `scripts/check_alerts.py` selon un planning
cron, indépendamment de l'état de l'app Streamlit.

1. Dans votre dépôt GitHub → **Settings → Secrets and variables → Actions**, ajoutez :
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
2. Activez/désactivez les types d'alerte depuis la page **🔔 Alertes** de l'app (bouton
   "Enregistrer la configuration" — écrit dans `alerts_config.json`, à committer/pousser pour que
   GitHub Actions en tienne compte), ou éditez directement ce fichier.
3. Le workflow tourne toutes les 15 minutes sur les horaires de marché (ajustable dans le fichier
   `.yml`) et peut aussi être lancé manuellement via l'onglet **Actions → Run workflow**.

## Structure du projet

```
app.py                          Page d'accueil / configuration du ticker
pages/
  1_📊_Graphiques.py
  2_ℹ️_Info.py
  3_🔔_Alertes.py
  4_📐_Support_Résistance.py
  5_🌀_Fibonacci.py
utils/
  data.py                       Récupération des données (Yahoo Finance)
  indicators.py                 EMA, VWAP, RSI, taille moyenne des bougies
  charts.py                     Graphiques chandeliers Plotly
  levels.py                     Support/résistance, Fibonacci
  telegram_utils.py             Envoi de notifications Telegram
scripts/
  check_alerts.py               Script autonome pour GitHub Actions
.github/workflows/check_alerts.yml
alerts_config.json              État des alertes activées
```

## Notes techniques

- Les données proviennent de Yahoo Finance via `yfinance`. Les limites de Yahoo s'appliquent :
  historique 5 min limité à ~60 jours, H1 à ~730 jours.
- Le H4 n'existe pas nativement chez Yahoo : il est reconstruit par ré-échantillonnage du H1.
- La "taille moyenne des bougies" (page Info) est la moyenne de `Haut − Bas` sur 14 jours — ce
  n'est **pas** l'ATR (qui intègre les gaps via le close précédent).
- Les niveaux support/résistance sont calculés sur les points pivots (extrêmes locaux) des 5
  derniers jours, regroupés par proximité, et ne retiennent que ceux touchés ≥ 2 fois.

## Avertissement

Cet outil est fourni à titre informatif et éducatif uniquement. Il ne constitue pas un conseil en
investissement. Toute décision de trading relève de votre seule responsabilité.
