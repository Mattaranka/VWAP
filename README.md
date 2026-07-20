# 📈 Dashboard PEA — Swing Trading multi-titres

Application Streamlit de suivi de plusieurs titres éligibles PEA, avec watchlist, graphiques
multi-timeframes, indicateurs clés, alertes Telegram, support/résistance et niveaux de
Fibonacci. Le titre initial est Nanobiotix (`NANO.PA`).

## Fonctionnalités

- **📋 Watchlist** : liste de titres suivis (ajout/retrait), tableau de synthèse quotidien
  (tendance D1, RSI, écart aux EMA20/50, volume vs moyenne 20j, support/résistance)
- **📊 Graphiques** : D1, H4 (reconstruit à partir du H1), H1, M5 — EMA 8/20/50/200 + VWAP,
  pour le titre actif
- **ℹ️ Info** : prix actuel, volume moyen 20j, volume du jour, plus haut/bas 52 semaines et
  5 jours, taille moyenne des bougies (en € et en %), hausse/baisse moyenne des mèches par
  rapport à l'ouverture, RSI journalier, VWAP de la session en cours
- **🔔 Alertes** : notifications Telegram par titre, activables/désactivables (croisements
  EMA8/EMA20 en M5/H1/D1, contact avec EMA20/50/200 en D1, RSI D1 hors zone 30-70, volume
  journalier > 1.5x la moyenne 20j)
- **📐 Support / Résistance** : graphique multi-périodes (1j à 1an), EMA et VWAP
  affichables/masquables, niveaux basés sur les points pivots touchés ≥ 2 fois sur 5 jours
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

## Alertes automatiques multi-titres via GitHub Actions (recommandé)

Le fichier `.github/workflows/check_alerts.yml` exécute `scripts/check_alerts.py` selon un
planning cron, en boucle sur tous les titres de la watchlist ayant au moins une alerte
activée — indépendamment de l'état de l'app Streamlit.

1. Dans votre dépôt GitHub → **Settings → Secrets and variables → Actions**, ajoutez :
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
2. Dans **Settings → Actions → General → Workflow permissions**, cochez **"Read and write
   permissions"** (le script committe l'état des alertes après chaque exécution, pour ne
   jamais manquer ni dupliquer une alerte).
3. Ajoutez vos titres depuis la page **📋 Watchlist**, puis activez les alertes voulues pour
   chacun depuis la page **🔔 Alertes** ("Enregistrer la configuration" — écrit dans
   `alerts_config.json`, à committer/pousser sur GitHub pour que le workflow en tienne compte).
4. Le workflow tourne toutes les 15 minutes sur les horaires de marché (ajustable dans le
   fichier `.yml`) et peut aussi être lancé manuellement via l'onglet **Actions → Run workflow**.

## Structure du projet

```
app.py                              Page d'accueil / sélection du titre actif
pages/
  0_📋_Watchlist.py                 Vue d'ensemble multi-titres
  1_📊_Graphiques.py
  2_ℹ️_Info.py
  3_🔔_Alertes.py                   Configuration des alertes par titre
  4_📐_Support_Résistance.py
  5_🌀_Fibonacci.py
utils/
  data.py                           Récupération des données (Yahoo Finance)
  indicators.py                     EMA, VWAP, RSI, statistiques de bougies
  charts.py                         Graphiques chandeliers Plotly
  levels.py                         Support/résistance, Fibonacci
  telegram_utils.py                 Envoi de notifications Telegram
  watchlist.py                      Gestion de la liste de titres suivis
  alerts_store.py                   Config/état des alertes, par titre
  screener.py                       Calculs de synthèse pour la Watchlist
scripts/
  check_alerts.py                   Script autonome pour GitHub Actions (boucle multi-titres)
.github/workflows/check_alerts.yml
watchlist.json                      Liste des titres suivis
alerts_config.json                  Alertes activées, par titre
alerts_state.json                   État courant des alertes, par titre (anti-doublon/anti-oubli)
```

## Notes techniques

- Les données proviennent de Yahoo Finance via `yfinance`. Historique 5 min limité à ~60 jours,
  H1 à ~730 jours.
- Le H4 n'existe pas nativement chez Yahoo : il est reconstruit par ré-échantillonnage du H1.
- La "taille moyenne des bougies" (page Info) est la moyenne de `Haut − Bas` sur 14 jours, en €
  et en % du prix d'ouverture — ce n'est **pas** l'ATR. Les "mèches" (hausse/baisse moyenne)
  sont calculées par rapport au prix d'ouverture, pas par rapport au corps de la bougie.
- Les alertes de croisement/contact/RSI sont déclenchées sur un **changement d'état** (et non
  sur la comparaison des deux dernières bougies), pour ne rien manquer entre deux vérifications
  ni spammer tant que l'état reste inchangé.
- Les niveaux support/résistance sont calculés sur les points pivots (extrêmes locaux) des 5
  derniers jours, regroupés par proximité, et ne retiennent que ceux touchés ≥ 2 fois.

## Avertissement

Cet outil est fourni à titre informatif et éducatif uniquement. Il ne constitue pas un conseil en
investissement, ni une confirmation d'éligibilité PEA. Toute décision de trading, ainsi que la
vérification de l'éligibilité PEA de chaque titre auprès de votre courtier, relève de votre seule
responsabilité.

