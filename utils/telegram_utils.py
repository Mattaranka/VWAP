"""Envoi de notifications Telegram.

Les identifiants peuvent être fournis via variables d'environnement
(TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) — utilisé par le script cron GitHub Actions —
ou via st.secrets["telegram"] — utilisé par l'application Streamlit.
"""
import os
import requests


def _get_credentials():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        return token, chat_id
    try:
        import streamlit as st
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        return token, chat_id
    except Exception:
        return None, None


def send_telegram_message(text: str):
    token, chat_id = _get_credentials()
    if not token or not chat_id:
        return False, "Configuration Telegram manquante (secrets.toml ou variables d'environnement)"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)
