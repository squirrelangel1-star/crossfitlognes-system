"""
Module Google Sheets — Mise à jour des onglets
"""

import os
import json
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

SCOPES    = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID  = os.environ["GOOGLE_SHEET_ID"]

# Noms des onglets
ONGLET_MEMBRES    = "MEMBRES"
ONGLET_STATS      = "STATS_MENSUELLES"
ONGLET_ALERTES    = "ALERTES"
ONGLET_LEADERBOARD= "LEADERBOARD"


def _get_service():
    creds_json = os.environ["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def mettre_a_jour_sheets(stats: dict, absences: dict, leaderboard: list):
    """Met à jour tous les onglets du Google Sheet central."""
    service = _get_service()
    sheets  = service.spreadsheets()

    _maj_membres(sheets, stats)
    _maj_stats_mensuelles(sheets, stats)
    _maj_alertes(sheets, absences)
    _maj_leaderboard(sheets, leaderboard)
    log.info("✅ Google Sheets mis à jour")


def _maj_membres(sheets, stats: dict):
    """Met à jour l'onglet MEMBRES."""
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    entetes = [
        "Identifiant", "Prénom", "Nom", "Email", "Téléphone",
        "Abonnement", "Expiration abo", "Créneaux carte",
        "Expiration carte", "Est payant", "Séances mois",
        "Dernière présence", "Jours absence", "Mis à jour"
    ]
    lignes = [entetes]
    for s in stats.values():
        lignes.append([
            s["identifiant"],
            s["prenom"],
            s["nom"],
            s["email"],
            s["telephone"],
            s["abonnement"] or "",
            str(s["abo_expiration"]) if s["abo_expiration"] else "",
            s["carte_creneaux"] if s["carte_creneaux"] is not None else "",
            str(s["carte_expiration"]) if s["carte_expiration"] else "",
            "Oui" if s["est_payant"] else "Non",
            s["seances_mois_actuel"],
            s["derniere_presence"] or "",
            s["jours_absence"] if s["jours_absence"] != 9999 else "Jamais venu",
            today,
        ])
    _ecrire_onglet(sheets, ONGLET_MEMBRES, lignes)
    log.info(f"✅ Onglet MEMBRES — {len(lignes)-1} membres")


def _maj_stats_mensuelles(sheets, stats: dict):
    """Met à jour l'onglet STATS_MENSUELLES."""
    entetes = ["Identifiant", "Prénom", "Nom"]
    # Collecter tous les mois disponibles
    tous_mois = set()
    for s in stats.values():
        tous_mois.update(s["seances_par_mois"].keys())
    mois_tries = sorted(tous_mois)
    entetes += mois_tries

    lignes = [entetes]
    for s in stats.values():
        if not s["est_payant"]:
            continue
        ligne = [s["identifiant"], s["prenom"], s["nom"]]
        ligne += [s["seances_par_mois"].get(m, 0) for m in mois_tries]
        lignes.append(ligne)

    _ecrire_onglet(sheets, ONGLET_STATS, lignes)
    log.info(f"✅ Onglet STATS_MENSUELLES — {len(lignes)-1} membres")


def _maj_alertes(sheets, absences: dict):
    """Met à jour l'onglet ALERTES."""
    today = datetime.now().strftime("%d/%m/%Y")
    entetes = [
        "Niveau", "Identifiant", "Prénom", "Nom",
        "Téléphone", "Email", "Jours absence",
        "Dernière présence", "Abonnement", "Date alerte"
    ]
    lignes = [entetes]

    for niveau, membres in absences.items():
        for m in membres:
            lignes.append([
                f"absent_{niveau}",
                m["identifiant"],
                m["prenom"],
                m["nom"],
                m["telephone"],
                m["email"],
                m["jours_absence"],
                m["derniere_presence"] or "",
                m["abonnement"] or "",
                today,
            ])

    _ecrire_onglet(sheets, ONGLET_ALERTES, lignes)
    log.info(f"✅ Onglet ALERTES — {len(lignes)-1} alertes")


def _maj_leaderboard(sheets, leaderboard: list):
    """Met à jour l'onglet LEADERBOARD."""
    today = datetime.now()
    entetes = [
        "Rang", "Prénom", "Nom initial", "Séances ce mois",
        "Séances mois précédent", "Progression", "Mois"
    ]
    mois_label = f"{today.strftime('%B')} {today.year}"
    lignes = [entetes]
    for m in leaderboard:
        lignes.append([
            m["rang"],
            m["prenom"],
            m["nom_initial"],
            m["seances"],
            m["seances_prec"],
            m["progression"],
            mois_label,
        ])

    _ecrire_onglet(sheets, ONGLET_LEADERBOARD, lignes)
    log.info(f"✅ Onglet LEADERBOARD — {len(leaderboard)} membres")


def _ecrire_onglet(sheets, nom_onglet: str, lignes: list):
    """Efface et réécrit un onglet entier."""
    plage = f"{nom_onglet}!A1"
    # Effacer d'abord
    sheets.values().clear(
        spreadsheetId=SHEET_ID,
        range=f"{nom_onglet}!A:Z"
    ).execute()
    # Écrire les nouvelles données
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range=plage,
        valueInputOption="RAW",
        body={"values": [[str(c) if c is not None else "" for c in ligne] for ligne in lignes]}
    ).execute()
