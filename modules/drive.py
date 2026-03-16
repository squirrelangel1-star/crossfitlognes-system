"""
Module Google Drive — Upload et téléchargement des fichiers
"""

import os
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import io

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

FOLDER_ID = os.environ["GOOGLE_DRIVE_FOLDER_ID"]


def _get_service():
    """Initialise le service Google Drive depuis les credentials JSON."""
    creds_json = os.environ["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def uploader_fichiers(fichiers: dict):
    """
    Upload les fichiers Excel vers Google Drive.
    fichiers = { nom: chemin_local }
    """
    service = _get_service()

    for nom, chemin in fichiers.items():
        nom_fichier = f"{nom}.xlsx"

        # Vérifier si le fichier existe déjà
        results = service.files().list(
            q=f"name='{nom_fichier}' and '{FOLDER_ID}' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        existants = results.get("files", [])

        media = MediaFileUpload(
            chemin,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        if existants:
            # Mettre à jour le fichier existant
            file_id = existants[0]["id"]
            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            log.info(f"✅ {nom_fichier} mis à jour sur Drive")
        else:
            # Créer un nouveau fichier
            metadata = {
                "name": nom_fichier,
                "parents": [FOLDER_ID]
            }
            service.files().create(
                body=metadata,
                media_body=media,
                fields="id"
            ).execute()
            log.info(f"✅ {nom_fichier} créé sur Drive")


def telecharger_fichiers() -> dict:
    """
    Télécharge les fichiers depuis Google Drive vers tmp/.
    Retourne { nom: chemin_local }
    """
    service = _get_service()
    fichiers = {}
    noms = ["utilisateurs", "abonnements", "cartes", "presences"]

    os.makedirs("tmp/downloads", exist_ok=True)

    for nom in noms:
        nom_fichier = f"{nom}.xlsx"
        results = service.files().list(
            q=f"name='{nom_fichier}' and '{FOLDER_ID}' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        fichiers_trouves = results.get("files", [])

        if not fichiers_trouves:
            log.warning(f"⚠️ {nom_fichier} non trouvé sur Drive")
            continue

        file_id = fichiers_trouves[0]["id"]
        chemin  = f"tmp/downloads/{nom_fichier}"

        request = service.files().get_media(fileId=file_id)
        with open(chemin, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        fichiers[nom] = chemin
        log.info(f"✅ {nom_fichier} téléchargé")

    return fichiers
