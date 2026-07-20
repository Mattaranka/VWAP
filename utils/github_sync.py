"""Synchronisation directe des fichiers de configuration vers GitHub, pour que l'app
Streamlit et le workflow GitHub Actions restent alignés sans étape manuelle.

Nécessite un token GitHub avec droit d'écriture sur le dépôt, renseigné dans
st.secrets["github"] :
    [github]
    token = "..."          # Personal Access Token (voir README pour la création)
    repo = "utilisateur/nom-du-repo"
    branch = "main"        # optionnel, "main" par défaut

Si non configuré, les fonctions renvoient simplement (False, ...) sans lever d'exception —
l'app continue de fonctionner en mode "sauvegarde locale uniquement".
"""
import base64
import json

import requests

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


def _get_github_config():
    if st is None:
        return None
    try:
        return {
            "token": st.secrets["github"]["token"],
            "repo": st.secrets["github"]["repo"],
            "branch": st.secrets["github"].get("branch", "main"),
        }
    except Exception:
        return None


def is_configured() -> bool:
    return _get_github_config() is not None


def push_file(path: str, content_str: str, commit_message: str):
    """Crée ou met à jour un fichier texte dans le dépôt GitHub via l'API Contents.
    Retourne (True, "") en cas de succès, (False, message_erreur) sinon."""
    cfg = _get_github_config()
    if cfg is None:
        return False, "Synchronisation GitHub non configurée (voir README)."

    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github+json",
    }

    sha = None
    try:
        r = requests.get(url, headers=headers, params={"ref": cfg["branch"]}, timeout=10)
        if r.status_code == 200:
            sha = r.json().get("sha")
        elif r.status_code != 404:
            return False, f"Lecture GitHub échouée ({r.status_code}) : {r.text[:200]}"
    except Exception as e:
        return False, str(e)

    payload = {
        "message": commit_message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": cfg["branch"],
    }
    if sha:
        payload["sha"] = sha

    try:
        r = requests.put(url, headers=headers, data=json.dumps(payload), timeout=10)
        if r.status_code in (200, 201):
            return True, ""
        return False, f"Écriture GitHub échouée ({r.status_code}) : {r.text[:200]}"
    except Exception as e:
        return False, str(e)
