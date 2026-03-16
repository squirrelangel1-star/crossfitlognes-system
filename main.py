"""
CrossFit CLC — Système automatisé de fidélisation
Script principal — tourne chaque nuit sur Railway.app
"""

import os
import logging
from datetime import datetime
from modules.resawod import exporter_resawod
from modules.drive import uploader_fichiers, telecharger_fichiers
from modules.calculs import calculer_stats, detecter_absences, generer_leaderboard
from modules.sheets import mettre_a_jour_sheets
from modules.ghl import synchroniser_ghl
from modules.leaderboard_json import generer_json_leaderboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/run.log")
    ]
)
log = logging.getLogger(__name__)

def run():
    log.info("="*60)
    log.info(f"DÉMARRAGE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("="*60)

    # ── ÉTAPE 1 : Export Resawod via Playwright ──────────────────
    log.info("ÉTAPE 1 — Export Resawod")
    try:
        fichiers = exporter_resawod()
        log.info(f"✅ {len(fichiers)} fichiers exportés depuis Resawod")
    except Exception as e:
        log.error(f"❌ Erreur export Resawod : {e}")
        raise

    # ── ÉTAPE 2 : Upload vers Google Drive ───────────────────────
    log.info("ÉTAPE 2 — Upload Google Drive")
    try:
        uploader_fichiers(fichiers)
        log.info("✅ Fichiers uploadés sur Google Drive")
    except Exception as e:
        log.error(f"❌ Erreur upload Drive : {e}")
        raise

    # ── ÉTAPE 3 : Calculs stats + absences + leaderboard ─────────
    log.info("ÉTAPE 3 — Calcul des statistiques")
    try:
        stats = calculer_stats(fichiers)
        absences = detecter_absences(fichiers)
        leaderboard = generer_leaderboard(fichiers)
        log.info(f"✅ Stats calculées — {len(absences['7j'])} absents 7j, {len(absences['14j'])} absents 14j, {len(absences['21j'])} absents 21j+")
        log.info(f"✅ Leaderboard généré — Top 1 : {leaderboard[0]['prenom'] if leaderboard else 'N/A'}")
    except Exception as e:
        log.error(f"❌ Erreur calculs : {e}")
        raise

    # ── ÉTAPE 4 : Mise à jour Google Sheets ──────────────────────
    log.info("ÉTAPE 4 — Mise à jour Google Sheets")
    try:
        mettre_a_jour_sheets(stats, absences, leaderboard)
        log.info("✅ Google Sheets mis à jour")
    except Exception as e:
        log.error(f"❌ Erreur Sheets : {e}")
        raise

    # ── ÉTAPE 5 : Génération JSON leaderboard public ─────────────
    log.info("ÉTAPE 5 — Génération JSON leaderboard")
    try:
        generer_json_leaderboard(leaderboard, stats)
        log.info("✅ JSON leaderboard généré et pushé sur GitHub")
    except Exception as e:
        log.error(f"❌ Erreur JSON leaderboard : {e}")
        raise

    # ── ÉTAPE 6 : Synchronisation GoHighLevel ────────────────────
    log.info("ÉTAPE 6 — Synchronisation GoHighLevel")
    try:
        resultats_ghl = synchroniser_ghl(stats, absences)
        log.info(f"✅ GHL synchronisé — {resultats_ghl['tags_mis_a_jour']} tags, {resultats_ghl['sequences_declenchees']} séquences déclenchées")
    except Exception as e:
        log.error(f"❌ Erreur GHL : {e}")
        raise

    log.info("="*60)
    log.info(f"✅ TERMINÉ — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("="*60)

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("tmp", exist_ok=True)
    run()
