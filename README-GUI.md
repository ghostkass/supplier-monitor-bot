# Interface graphique (Streamlit)

## Installation
```
pip install -r requirements.txt
```

## Lancer le dashboard
```
streamlit run ui/app.py
```
Ouvre le navigateur (localhost) pour accéder au tableau de bord.

## Fonctionnalités
- Bouton **Lancer une vérification maintenant** (appelle `monitor.run_once()`).
- Vue produits + filtres, derniers changements, historiques (prix/stock) avec graphiques.
- Boutons de **test d'email** et **test WhatsApp**.
- Thème sombre moderne (configurable via `ui/.streamlit/config.toml`).

> Pour la planification, lance en parallèle : `python monitor.py run-daemon --every-hours 3`.
