# CrossFit CLC — Système automatisé de fidélisation

Script Python tournant sur Railway.app chaque nuit à 3h pour :
- Exporter automatiquement les données depuis Resawod (Playwright)
- Calculer les stats, absences et leaderboard
- Mettre à jour Google Sheets
- Pousser le leaderboard JSON sur GitHub Pages
- Déclencher les séquences WhatsApp via GoHighLevel

## Architecture

```
Resawod (Playwright)
    → Google Drive (stockage fichiers)
    → Calculs Python (stats + absences + leaderboard)
    → Google Sheets (base de données centrale)
    → GitHub Pages (leaderboard public)
    → GoHighLevel (tags + séquences WhatsApp)
```

## Installation Railway

1. Connecter ce dépôt GitHub à Railway
2. Configurer toutes les variables d'environnement (voir .env.example)
3. Définir le Build Command : `bash build.sh`
4. Configurer le Cron Job : `0 3 * * *` (chaque nuit à 3h)

## Variables d'environnement requises

Voir `.env.example` pour la liste complète.

## Basculer vers l'API Nubapp

Quand les credentials API Nubapp sont disponibles :
1. Ajouter `NUBAPP_JWT_TOKEN` et `NUBAPP_APP_ID` dans Railway
2. Modifier `main.py` pour utiliser `modules/api_nubapp.py` 
   à la place de `modules/resawod.py`

## Structure des fichiers

```
main.py                     Script principal
modules/
    resawod.py              Export Playwright
    drive.py                Google Drive
    sheets.py               Google Sheets
    calculs.py              Logique métier
    ghl.py                  GoHighLevel
    leaderboard_json.py     JSON public
    api_nubapp.py           API Nubapp (futur)
docs/
    leaderboard.json        Données leaderboard public
    index.html              Page web leaderboard
```
