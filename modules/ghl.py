"""
Module GoHighLevel — Synchronisation tags et déclenchement séquences WhatsApp
"""

import os
import logging
import requests
from datetime import datetime

log = logging.getLogger(__name__)

GHL_API_KEY     = os.getenv["GHL_API_KEY"]
GHL_LOCATION_ID = os.environ["GHL_LOCATION_ID"]

BASE_URL = "https://rest.gohighlevel.com/v1"
HEADERS  = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type":  "application/json"
}

# Mapping tags selon niveau d'absence
TAGS_ABSENCE = {
    "7j":  "absent_7j",
    "14j": "absent_14j",
    "21j": "absent_21j",
}

# IDs des workflows GHL à déclencher (à renseigner dans .env)
WORKFLOW_ABSENT_7J  = os.environ.get("GHL_WORKFLOW_ABSENT_7J", "")
WORKFLOW_ABSENT_14J = os.environ.get("GHL_WORKFLOW_ABSENT_14J", "")
WORKFLOW_ABSENT_21J = os.environ.get("GHL_WORKFLOW_ABSENT_21J", "")
WORKFLOW_CARNET_VIDE= os.environ.get("GHL_WORKFLOW_CARNET_VIDE", "")


def synchroniser_ghl(stats: dict, absences: dict) -> dict:
    """
    Synchronise les données avec GoHighLevel :
    1. Met à jour les tags de chaque membre payant
    2. Déclenche les séquences WhatsApp pour les absents
    3. Alerte pour les carnets épuisés et abonnements expirant
    """
    tags_mis_a_jour      = 0
    sequences_declenchees = 0

    # ── 1. Mise à jour des tags abonnements ──────────────────────
    for idd, s in stats.items():
        if not s["est_payant"] or not s["telephone"]:
            continue
        try:
            contact = _trouver_contact(s["telephone"], s["email"])
            if contact:
                tags = _calculer_tags(s)
                _mettre_a_jour_tags(contact["id"], tags)
                tags_mis_a_jour += 1
        except Exception as e:
            log.warning(f"⚠️ Erreur tag GHL pour {s['prenom']} {s['nom']} : {e}")

    # ── 2. Déclencher séquences absences ─────────────────────────
    workflows = {
        "7j":  WORKFLOW_ABSENT_7J,
        "14j": WORKFLOW_ABSENT_14J,
        "21j": WORKFLOW_ABSENT_21J,
    }

    for niveau, membres in absences.items():
        workflow_id = workflows.get(niveau, "")
        if not workflow_id:
            log.warning(f"⚠️ Workflow GHL absent_{niveau} non configuré — séquence ignorée")
            continue

        for m in membres:
            if not m["telephone"]:
                continue
            try:
                contact = _trouver_contact(m["telephone"], m["email"])
                if contact:
                    _declencher_workflow(contact["id"], workflow_id)
                    sequences_declenchees += 1
                    log.info(f"📱 Séquence absent_{niveau} → {m['prenom']} {m['nom']}")
            except Exception as e:
                log.warning(f"⚠️ Erreur workflow GHL {m['prenom']} : {e}")

    # ── 3. Alertes carnets épuisés ────────────────────────────────
    if WORKFLOW_CARNET_VIDE:
        for idd, s in stats.items():
            if s["carte_creneaux"] == 0 and s["telephone"]:
                try:
                    contact = _trouver_contact(s["telephone"], s["email"])
                    if contact:
                        _declencher_workflow(contact["id"], WORKFLOW_CARNET_VIDE)
                        sequences_declenchees += 1
                        log.info(f"📱 Séquence carnet_vide → {s['prenom']} {s['nom']}")
                except Exception as e:
                    log.warning(f"⚠️ Erreur workflow carnet {s['prenom']} : {e}")

    return {
        "tags_mis_a_jour":       tags_mis_a_jour,
        "sequences_declenchees": sequences_declenchees,
    }


def _trouver_contact(telephone: str, email: str) -> dict | None:
    """Cherche un contact dans GHL par téléphone puis email."""
    # Recherche par téléphone
    if telephone:
        r = requests.get(
            f"{BASE_URL}/contacts/",
            headers=HEADERS,
            params={"locationId": GHL_LOCATION_ID, "query": telephone}
        )
        if r.status_code == 200:
            contacts = r.json().get("contacts", [])
            if contacts:
                return contacts[0]

    # Fallback : recherche par email
    if email:
        r = requests.get(
            f"{BASE_URL}/contacts/",
            headers=HEADERS,
            params={"locationId": GHL_LOCATION_ID, "query": email}
        )
        if r.status_code == 200:
            contacts = r.json().get("contacts", [])
            if contacts:
                return contacts[0]

    return None


def _calculer_tags(s: dict) -> list:
    """Calcule les tags à appliquer selon le profil du membre."""
    tags = []

    # Tag abonnement
    abo = s.get("abonnement", "")
    if abo:
        if "Illimité" in abo or "iIlimité" in abo:
            tags.append("abo_illimite")
        elif "2x" in abo:
            tags.append("abo_limite_2x")
        elif "3x" in abo:
            tags.append("abo_limite_3x")
        elif "Premium" in abo:
            tags.append("abo_premium")
        elif "pause" in abo.lower():
            tags.append("abo_pause")
        elif "Teens" in abo or "Kids" in abo:
            tags.append("abo_kids_teens")

    # Tag carte
    if s.get("carte_creneaux", 0) > 0:
        tags.append("abo_carte")
    elif s.get("carte_creneaux") == 0:
        tags.append("carnet_vide")

    # Tag absence
    j = s.get("jours_absence", 0)
    if j >= 21:
        tags.append("absent_21j")
    elif j >= 14:
        tags.append("absent_14j")
    elif j >= 7:
        tags.append("absent_7j")

    # Tag expiration proche (30 jours)
    exp = s.get("abo_expiration")
    if exp and exp != "Illimité":
        try:
            date_exp = datetime.strptime(str(exp), "%d-%m-%Y")
            jours_exp = (date_exp - datetime.now()).days
            if jours_exp <= 30:
                tags.append("expiration_proche")
        except:
            pass

    return tags


def _mettre_a_jour_tags(contact_id: str, tags: list):
    """Met à jour les tags d'un contact GHL."""
    requests.put(
        f"{BASE_URL}/contacts/{contact_id}",
        headers=HEADERS,
        json={"tags": tags}
    )


def _declencher_workflow(contact_id: str, workflow_id: str):
    """Déclenche un workflow GHL pour un contact."""
    requests.post(
        f"{BASE_URL}/contacts/{contact_id}/workflow/{workflow_id}",
        headers=HEADERS,
        json={}
    )
