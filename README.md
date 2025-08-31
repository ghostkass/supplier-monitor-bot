<img width="1885" height="855" alt="Screenshot 2025-08-31 175225" src="https://github.com/user-attachments/assets/13afcfe2-7230-4370-9dc4-f867501c6f52" />

<img width="1541" height="860" alt="Screenshot 2025-08-31 175242" src="https://github.com/user-attachments/assets/06412070-d424-48ff-b2c0-934a60f5a529" />


# Supplier Monitor Bot — README Complet

Un bot Python pour **surveiller les pages produits** de vos fournisseurs (Amazon, AliExpress, Alibaba, etc.) et **vous alerter** lorsque :
- le **prix change** ;
- le **stock** évolue ou tombe à **zéro** ;
- le produit devient **indisponible** ;
- la **page disparaît** (404/410 ou message équivalent).

Le système conserve l’**historique**, notifie par **Email** et/ou **WhatsApp (Twilio)** et propose une **interface graphique moderne** (Streamlit).

---

## 🧱 Pile technique
- **Python** (3.12 recommandé — 3.13 OK avec petits ajustements)
- **Scraping statique** : `requests` + `BeautifulSoup`
- **Scraping dynamique** : `playwright` (Chromium headless)
- **Base de données** : `SQLAlchemy` (SQLite par défaut, MySQL possible)
- **Planification** : `schedule` (daemon) ou **cron / Windows Task Scheduler**
- **Notifications** : SMTP (Gmail App Password) & **Twilio/WhatsApp**
- **Historique & export** : CSV (`logs/changes.csv`) + Excel via CLI
- **UI** : Streamlit + Plotly (tableaux, filtres, graphiques, boutons d’action)

---

## 📁 Structure du projet (principaux dossiers/fichiers)
```
supplier-monitor-bot/
├─ config/
│  └─ vendors.yaml            # Sélecteurs par domaine (prix/stock/dispo)
├─ data/
│  └─ products.csv            # Base produits initiale (importable via CLI)
├─ logs/
│  └─ changes.csv             # Historique des changements
├─ notifiers/
│  ├─ email_notifier.py       # SMTP (Gmail App Password requis)
│  └─ twilio_notifier.py      # WhatsApp (Twilio)
├─ scrapers/
│  ├─ base_scraper.py         # Classe de base
│  ├─ static_scraper.py       # requests + BeautifulSoup
│  └─ dynamic_scraper.py      # Playwright (JS)
├─ store/
│  ├─ db.py                   # Connexion SQLAlchemy
│  └─ models.py               # Product, Snapshot, ChangeEvent
├─ ui/
│  ├─ app.py                  # Dashboard Streamlit
│  └─ .streamlit/config.toml  # Thème
├─ utils/
│  ├─ price.py                # parse_price()
│  └─ text_norm.py            # normalize_text()
├─ cli.py                     # Gestion produits + export Excel
├─ monitor.py                 # run-once / run-daemon (planifié)
├─ README_FULL.md             # (ce fichier)
├─ README-GUI.md              # Guide UI Streamlit
├─ requirements.txt
├─ .env.example
└─ run_ui.bat                 # Lance l’UI (Windows, double-clic)
```

---

## ⚙️ Installation (Windows & Linux/Mac)

> **Conseil** : Python **3.12** recommandé (meilleur support des wheels). Ça fonctionne en 3.13 mais **lxml** peut demander un correctif (voir *Dépannage*).

```bash
# 1) Créer l’environnement virtuel
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 2) Installer les dépendances
pip install -r requirements.txt

# 3) Installer Playwright (navigateur headless)
python -m playwright install chromium
```

### Cas Windows/Python 3.13 (erreur lxml)
Si `pip` échoue à compiler **lxml** :
1) **Option rapide** : commente/supprime `lxml==...` dans `requirements.txt`  
   (Le code passe automatiquement en `html.parser` si `lxml` est absent).
2) **Option recommandée** : utiliser **Python 3.12**.

---

## 🔐 Configuration (.env)

Copiez `.env.example` → `.env` et renseignez :

```ini
# Base de données
DB_URL=sqlite:///supplier.db
# MySQL (exemple) : DB_URL=mysql+pymysql://user:pass@host:3306/supplier_db

# SMTP (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=ton_email@gmail.com
SMTP_PASSWORD=APP_PASSWORD_16_CARACTERES  # Mot de passe d'application Gmail
SMTP_FROM=ton_email@gmail.com
ALERT_TO=ton_email@gmail.com

# Twilio WhatsApp (sandbox)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
ALERT_TO_WHATSAPP=whatsapp:+22177xxxxxxx

# Parsing (optionnel)
CURRENCY_SYMBOLS=F CFA,FCFA,$,€,£
```

### Générer le **Gmail App Password**
- Active la **2FA** dans *Compte Google → Sécurité* ;
- Va dans **Mots de passe d’application** → choisis *Mail* → génère une clé **16 caractères** ;
- Mets-la dans `SMTP_PASSWORD` (jamais ton mot de passe normal).

### Twilio **WhatsApp Sandbox**
- Console Twilio → *Messaging → Try it out → WhatsApp Sandbox*
- Envoie `join <code>` depuis ton WhatsApp vers **le numéro sandbox** affiché (ex. `+14155238886`).
- Dans `.env`, **From** doit être **exactement** `whatsapp:+14155238886` (ou le tien), **To** ton numéro en E.164 : `whatsapp:+22177…`.

---

## 🗂️ Configuration des fournisseurs (`config/vendors.yaml`)

Chaque entrée décrit **comment extraire prix/stock/dispo** selon le **domaine** :

```yaml
vendors:
  - name: "Amazon (exemple)"
    domain: "amazon.com"
    dynamic: true           # page souvent en JS; Playwright conseillé
    wait_until: "networkidle"
    selectors:
      price: "#tp_price_block_total_price_ww, #priceblock_ourprice, #priceblock_dealprice, span.a-price > span.a-offscreen"
      availability: "#availability, #availabilityInsideBuyBox_feature_div"
      stock: "#availability, #quantity, span#availability span"
    out_of_stock_keywords: ["rupture", "épuisé", "indisponible", "out of stock", "sold out"]
    product_gone_keywords: ["404", "not found", "ce produit n'existe plus", "page not found"]

  - name: "AliExpress (exemple)"
    domain: "aliexpress.us" # ajoute aussi 'aliexpress.com' si besoin
    dynamic: true
    wait_until: "networkidle"
    selectors:
      price: ".product-price-value, .product-price-current, span#j-sku-price"
      availability: ".product-dynamic-shipping, .product-quantity-tip, .pdp-mod-product-banner"
      stock: ".product-quantity, .quantity, .product-quantity-tip"

  - name: "Alibaba (exemple)"
    domain: "alibaba.com"
    dynamic: true
    wait_until: "networkidle"
    selectors:
      price: ".price, .price-range, .offer-price"
      availability: ".supply-ability, .stock, .status"
      stock: ".stock, [data-stock]"
```

> Les sites évoluent : ajuste les sélecteurs dès que nécessaire. Tu peux lister **plusieurs** sélecteurs **séparés par des virgules** ; le premier qui “matche” est utilisé.

---

## 🗄️ Base de données & initialisation

### Créer les tables (si besoin)
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from store.db import engine, Base; Base.metadata.create_all(bind=engine); print('DB OK')"
```

### Importer des produits
```bash
python cli.py import-csv data/products.csv
# ...ou ajouter un produit :
python cli.py add --name "Produit X" --url "https://fournisseur.com/..." --vendor auto
```

### Lister / supprimer
```bash
python cli.py list
python cli.py remove --id 3
```

### Export Excel (produits, snapshots, changements)
```bash
python cli.py export-excel logs/changes.xlsx
```

---

## 🚀 Exécuter le bot

### Exécution ponctuelle
```bash
python monitor.py run-once
```

### Boucle planifiée (process long) — toutes les 3h
```bash
python monitor.py run-daemon --every-hours 3
```

### Cron (Linux)
```
0 */3 * * * /chemin/vers/python /chemin/vers/monitor.py run-once >> /chemin/vers/logs/cron.log 2>&1
```

### Windows Task Scheduler
Crée une tâche qui exécute :
```
D:\supplier-monitor-bot\.venv\Scripts\python.exe D:\supplier-monitor-bot\monitor.py run-once
```
toutes les X heures.

---

## 🖥️ Interface graphique (Streamlit)

### Installation des deps UI
Si `streamlit` et `plotly` ne sont pas dans `requirements.txt` :
```bash
pip install streamlit==1.38.0 plotly==5.23.0
# ou
pip install -r requirements-ui.txt
```

### Lancer le dashboard
```bash
streamlit run ui/app.py
```
Ou, sous Windows, **double-clique** `run_ui.bat` (fournit `PYTHONPATH`, crée la DB si besoin, lance l’UI).

Dans l’UI :
- **🔁 Lancer une vérification** : exécute `monitor.run_once()`
- **📧 Test Email / 💬 Test WhatsApp**
- **📦 Produits** : table filtrable (nom/URL)
- **🕒 Changements récents**
- **📈 Historique** : graphes prix/stock, table snapshots

---

## 🔔 Notifications

### Email (SMTP/Gmail)
- Utilise **Gmail App Password (16 caractères)** pour `SMTP_PASSWORD` ;
- `SMTP_FROM` = `SMTP_USERNAME` (recommandé) ;
- Test rapide :
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from notifiers.email_notifier import send_email; send_email('[TEST] Supplier Monitor','Ceci est un test SMTP.')"
```

### WhatsApp (Twilio)
- Rejoindre le **sandbox** (message `join <code>` au numéro Twilio affiché) ;
- `.env` :
  - `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886` (ou le tien) ;
  - `ALERT_TO_WHATSAPP=whatsapp:+22177…` (ton numéro) ;
- Test :
```bash
python test_whatsapp.py
```

**Erreur 63007 (Twilio)** : From invalide → vérifie le **préfixe `whatsapp:`** et que tu utilises **le numéro sandbox** (pas ton perso).

---

## 🧪 Journal & exports
- `logs/changes.csv` → Append-only : `timestamp, product_id, field, old_value, new_value, url, detail`
- `cli.py export-excel logs/changes.xlsx` → 3 onglets : `products`, `snapshots`, `changes`

---

## 🛠️ Dépannage (FAQ des erreurs courantes)

**No module named playwright**
```
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

**lxml: failed building wheel** (Windows / Python 3.13)  
→ Commente `lxml==...` dans `requirements.txt` (fallback `html.parser`), ou utilise **Python 3.12**.

**sqlite3.OperationalError: no such table: products**  
→ Crée les tables : `Base.metadata.create_all(bind=engine)` (voir plus haut) ; importe le CSV.

**ModuleNotFoundError: store** (quand tu lances `python ui/app.py`)  
→ Lance avec Streamlit depuis la racine, ou :
- ajoute en haut de `ui/app.py` :
  ```python
  from pathlib import Path, sys
  PROJECT_ROOT = Path(__file__).resolve().parents[1]
  sys.path.insert(0, str(PROJECT_ROOT))
  ```
- et crée les fichiers `__init__.py` dans `store/`, `scrapers/`, `notifiers/`, `utils/` ;
- le `run_ui.bat` fourni règle tout ça automatiquement.

**DeprecationWarning: datetime.utcnow()**  
→ Remplace par `datetime.now(UTC)` ; ajoute en haut :
```python
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone as _tz; UTC = _tz.utc
from datetime import datetime
```

**Email non reçu / [DRY-RUN]**  
→ `.env` incomplet (il manque `SMTP_PASSWORD` ou autre). Utilise un **Gmail App Password**.

**Twilio 63007**  
→ `TWILIO_WHATSAPP_FROM` doit être **le numéro sandbox** (avec `whatsapp:`), pas ton perso. Assure-toi d’avoir rejoint le sandbox.

**PowerShell refuse `Activate.ps1`**  
→ Lance les commandes avec le chemin complet vers `.venv\Scripts\python.exe`, ou exécute `Set-ExecutionPolicy -Scope Process Bypass` (si autorisé).

---

## 🔒 Sécurité & conformité
- Ne **committe** jamais `.env` (déjà dans `.gitignore`).
- Si tu partages un zip/backup, **retire** `.env` et `supplier.db`.
- Respecte toujours les **CGU** et **robots.txt** des sites scrappés, et les lois locales sur le scraping.
- Limite la charge : sleeps aléatoires, paging, cache, User-Agent, etc. (à étendre si besoin).

---

## 🧩 Extensions possibles
- Ajouter **XPaths** (via `lxml`/`parsel`) en plus des sélecteurs CSS ;
- Notifs **Telegram/Slack** en plus d’Email/WhatsApp ;
- Déduplication intelligente des alertes, seuils de bruit, regroupement ;
- Support **proxies** / rotation d’IP ;
- UI : **ajout produit** depuis le dashboard, **export Excel** 1 clic, upload **CSV** ;
- Back-end API (FastAPI) + Front (Next.js) pour une version serveur multi-utilisateur.

---

## 📜 Licence
Propriétaire / usage interne par défaut (adapter selon vos besoins).

---

## 📞 Support
Si tu bloques sur une étape (Windows, Twilio, Gmail App Password, Streamlit), décris l’erreur **exacte** et la commande exécutée — je te fournis le patch/conseil adapté.
