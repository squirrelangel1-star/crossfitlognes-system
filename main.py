"""
CrossFit CLC — Système automatisé de fidélisation v2
Script principal — tourne chaque nuit sur Railway.app
"""

import os
import logging
from datetime import datetime
from modules.resawod import exporter_resawod
from modules.calculs import calculer_stats, detecter_absences, generer_leaderboard
from modules.sheets import mettre_a_jour_sheets
from modules.leaderboard_json import generer_json_leaderboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

def run():
    log.info("="*60)
    log.info(f"DÉMARRAGE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("="*60)

    # ── ÉTAPE 1 : Export Resawod ──────────────────────────────────
    log.info("ÉTAPE 1 — Export Resawod")
    fichiers = exporter_resawod()
    log.info(f"✅ {len(fichiers)} fichiers exportés depuis Resawod")

    # ── ÉTAPE 2 : Calculs ─────────────────────────────────────────
    log.info("ÉTAPE 2 — Calcul des statistiques")
    stats    = calculer_stats(fichiers)
    absences = detecter_absences(fichiers)
    leaderboard = generer_leaderboard(fichiers)
    log.info(f"✅ Stats calculées — absents 7j:{len(absences['7j'])} 14j:{len(absences['14j'])} 21j+:{len(absences['21j'])}")

    # ── ÉTAPE 3 : Google Sheets ───────────────────────────────────
    log.info("ÉTAPE 3 — Mise à jour Google Sheets")
    mettre_a_jour_sheets(stats, absences, leaderboard)
    log.info("✅ Google Sheets mis à jour")

    # ── ÉTAPE 4 : Leaderboard JSON → GitHub ──────────────────────
    log.info("ÉTAPE 4 — Génération leaderboard JSON")
    generer_json_leaderboard(leaderboard, stats)
    log.info("✅ Leaderboard généré")

    # ── ÉTAPE 5 : GoHighLevel (optionnel) ─────────────────────────
    if os.environ.get("GHL_API_KEY"):
        log.info("ÉTAPE 5 — Synchronisation GoHighLevel")
        from modules.ghl import synchroniser_ghl
        resultats_ghl = synchroniser_ghl(stats, absences)
        log.info(f"✅ GHL — {resultats_ghl['tags_mis_a_jour']} tags, {resultats_ghl['sequences_declenchees']} séquences")
    else:
        log.info("ÉTAPE 5 — GHL non configuré — ignoré")

    log.info("="*60)
    log.info(f"✅ TERMINÉ — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("="*60)

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("tmp", exist_ok=True)
    run()
