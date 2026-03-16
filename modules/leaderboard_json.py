"""
Module Leaderboard JSON — Génère le fichier JSON public pour la page web
et le pousse sur GitHub Pages
"""

import os
import json
import logging
import requests
import base64
from datetime import datetime

log = logging.getLogger(__name__)

GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO     = os.environ.get("GITHUB_REPO", "squirrelangel1-star/crossfitlognes-system")
GITHUB_FILE     = "docs/leaderboard.json"
GITHUB_BRANCH   = "main"


def generer_json_leaderboard(leaderboard: list, stats: dict):
    """
    Génère le fichier leaderboard.json et le pousse sur GitHub.
    La page web lit ce fichier pour s'afficher.
    """
    today = datetime.now()

    # Calculer stats globales
    membres_actifs   = sum(1 for s in stats.values() if s["est_payant"])
    total_seances    = sum(s["seances_mois_actuel"] for s in stats.values())
    absents_7j       = sum(1 for s in stats.values() if s["est_payant"] and 7 <= s["jours_absence"] < 14)
    absents_14j      = sum(1 for s in stats.values() if s["est_payant"] and 14 <= s["jours_absence"] < 21)
    absents_21j      = sum(1 for s in stats.values() if s["est_payant"] and s["jours_absence"] >= 21)

    data = {
        "mis_a_jour":     today.strftime("%d/%m/%Y à %H:%M"),
        "mois":           today.strftime("%B %Y"),
        "mois_code":      f"{today.year}-{today.month:02d}",
        "stats_globales": {
            "membres_actifs":  membres_actifs,
            "seances_du_mois": total_seances,
            "absents_7j":      absents_7j,
            "absents_14j":     absents_14j,
            "absents_21j":     absents_21j,
        },
        "leaderboard": [
            {
                "rang":       m["rang"],
                "prenom":     m["prenom"],
                "initiale":   m["nom_initial"],
                "seances":    m["seances"],
                "progression":m["progression"],
            }
            for m in leaderboard
        ],
        "challenges": _calculer_challenges(stats),
    }

    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    # Sauvegarder localement
    os.makedirs("tmp", exist_ok=True)
    with open("tmp/leaderboard.json", "w", encoding="utf-8") as f:
        f.write(json_str)

    # Pousser sur GitHub si token disponible
    if GITHUB_TOKEN:
        try:
            _pousser_sur_github(json_str)
            log.info("✅ leaderboard.json pushé sur GitHub Pages")
        except Exception as e:
            log.warning(f"⚠️ Push GitHub échoué : {e} — JSON sauvegardé localement")
    else:
        log.warning("⚠️ GITHUB_TOKEN non configuré — JSON sauvegardé localement uniquement")


def _calculer_challenges(stats: dict) -> dict:
    """Calcule les statistiques des challenges du mois."""
    today = datetime.now()
    mois  = f"{today.year}-{today.month:02d}"

    challenge_12     = 0  # 12 séances dans le mois
    challenge_regulier = 0  # 2 séances/semaine (approx : 8 séances/mois)
    challenge_progress = 0  # Plus de séances que le mois précédent

    mois_prec = _mois_precedent(today)

    for s in stats.values():
        if not s["est_payant"]:
            continue
        nb_mois = s["seances_par_mois"].get(mois, 0)
        nb_prec = s["seances_par_mois"].get(mois_prec, 0)

        if nb_mois >= 12:
            challenge_12 += 1
        if nb_mois >= 8:
            challenge_regulier += 1
        if nb_mois > nb_prec > 0:
            challenge_progress += 1

    return {
        "challenge_12_seances":  {"nom": "12 séances", "validations": challenge_12},
        "challenge_regulier":    {"nom": "Régulier (8+ séances)", "validations": challenge_regulier},
        "challenge_progression": {"nom": "Progression vs mois précédent", "validations": challenge_progress},
    }


def _pousser_sur_github(contenu: str):
    """Pousse le fichier JSON sur GitHub via l'API."""
    url     = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github.v3+json"
    }

    # Récupérer le SHA actuel si le fichier existe
    sha = None
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")

    # Préparer le payload
    payload = {
        "message": f"Update leaderboard — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "content": base64.b64encode(contenu.encode("utf-8")).decode("utf-8"),
        "branch":  GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise Exception(f"Erreur GitHub API : {r.status_code} — {r.text}")


def _mois_precedent(today: datetime) -> str:
    if today.month == 1:
        return f"{today.year - 1}-12"
    return f"{today.year}-{today.month - 1:02d}"
