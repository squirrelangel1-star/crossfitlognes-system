"""
Module API Nubapp — Prêt pour remplacement du Playwright
Activé automatiquement quand NUBAPP_JWT_TOKEN est défini dans les variables d'environnement.
"""

import os
import logging
import requests
from datetime import datetime

log = logging.getLogger(__name__)

NUBAPP_URL      = os.environ.get("RESAWOD_URL", "https://sport.nubapp.com")
NUBAPP_TOKEN    = os.environ.get("NUBAPP_JWT_TOKEN", "")
NUBAPP_APP_ID   = os.environ.get("NUBAPP_APP_ID", "")

def api_disponible() -> bool:
    """Vérifie si les credentials API Nubapp sont configurés."""
    return bool(NUBAPP_TOKEN and NUBAPP_APP_ID)


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {NUBAPP_TOKEN}",
        "Content-Type":  "application/json"
    }


def get_membres() -> list:
    """Récupère la liste complète des membres via l'API."""
    r = requests.post(
        f"{NUBAPP_URL}/api/v5/users/getUsers",
        headers=get_headers(),
        json={"id_application": NUBAPP_APP_ID}
    )
    r.raise_for_status()
    return r.json().get("users", [])


def get_abonnements() -> list:
    """Récupère les abonnements actifs."""
    r = requests.post(
        f"{NUBAPP_URL}/api/v5/subscriptions/getSubscriptions",
        headers=get_headers(),
        json={"id_application": NUBAPP_APP_ID, "status": "active"}
    )
    r.raise_for_status()
    return r.json().get("subscriptions", [])


def get_presences(date_debut: str, date_fin: str) -> list:
    """Récupère les présences sur une période donnée."""
    r = requests.post(
        f"{NUBAPP_URL}/api/v5/bookings/getBookings",
        headers=get_headers(),
        json={
            "id_application": NUBAPP_APP_ID,
            "date_start":     date_debut,
            "date_end":       date_fin,
        }
    )
    r.raise_for_status()
    return r.json().get("bookings", [])


def get_cartes() -> list:
    """Récupère les cartes prépayées actives."""
    r = requests.post(
        f"{NUBAPP_URL}/api/v5/prepaid_cards/getPrepaidCards",
        headers=get_headers(),
        json={"id_application": NUBAPP_APP_ID}
    )
    r.raise_for_status()
    return r.json().get("prepaid_cards", [])
