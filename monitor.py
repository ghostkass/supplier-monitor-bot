\
from __future__ import annotations
import os, sys, csv, json, time, hashlib, argparse
from datetime import datetime
from urllib.parse import urlparse
import yaml

from store.db import SessionLocal, Base, engine
from store.models import Product, Snapshot, ChangeEvent
from scrapers.static_scraper import StaticScraper
from scrapers.dynamic_scraper import DynamicScraper
from scrapers.base_scraper import BaseScraper
from utils.price import parse_price
from utils.text_norm import normalize_text
from notifiers.email_notifier import send_email
from notifiers.twilio_notifier import send_whatsapp

import pandas as pd

from dotenv import load_dotenv
load_dotenv()

CHANGES_CSV = os.path.join("logs", "changes.csv")

# ---------- Vendor config ----------
def load_vendor_config(path="config/vendors.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def pick_vendor(vendors_cfg, url: str):
    host = urlparse(url).hostname or ""
    for vendor in vendors_cfg.get("vendors", []):
        domain = vendor.get("domain", "")
        if domain and domain in host:
            return vendor
    # no direct match -> None (let caller decide 'auto' vs default generic)
    return None

# ---------- Scrape & parse ----------
def choose_scraper(vendor_cfg) -> BaseScraper:
    dynamic = vendor_cfg.get("dynamic", False) if vendor_cfg else False
    if dynamic:
        return DynamicScraper(wait_until=vendor_cfg.get("wait_until", "networkidle"))
    return StaticScraper()

def extract_texts(soup, selector: str):
    if not selector:
        return []
    # Support multi-selectors separated by commas
    results = []
    for sel in [s.strip() for s in selector.split(",")]:
        if not sel:
            continue
        if sel.startswith("//"):
            # XPath not supported in bs4 directly; ignore here for brevity or extend with parsel/lxml
            continue
        for el in soup.select(sel):
            txt = el.get_text(separator=" ", strip=True)
            if txt:
                results.append(txt)
    return results

def safe_hash_html(html: str) -> str:
    # compact/minify-ish to avoid trivial diffs
    import re
    minified = re.sub(r"\s+", " ", html or "").strip()
    return hashlib.sha256(minified.encode("utf-8", "ignore")).hexdigest()

def interpret_fields(vendor_cfg, soup, html_text: str):
    sels = (vendor_cfg or {}).get("selectors", {})
    price_candidates = extract_texts(soup, sels.get("price", ""))
    availability_candidates = extract_texts(soup, sels.get("availability", ""))
    stock_candidates = extract_texts(soup, sels.get("stock", ""))

    # Price
    price_val = None
    for t in price_candidates:
        p = parse_price(t)
        if p is not None:
            price_val = p
            break

    # Availability / stock text detection
    avail_text = " ".join(availability_candidates) if availability_candidates else ""
    stock_text = " ".join(stock_candidates) if stock_candidates else ""

    norm_all = normalize_text(avail_text + " " + stock_text + " " + (html_text[:5000] if html_text else ""))
    oos_kw = [k.lower() for k in (vendor_cfg or {}).get("out_of_stock_keywords", [])]
    gone_kw = [k.lower() for k in (vendor_cfg or {}).get("product_gone_keywords", [])]

    status = "available"
    if any(k in norm_all for k in gone_kw):
        status = "gone"
    elif any(k in norm_all for k in oos_kw):
        status = "unavailable"

    # Try to detect numeric stock
    stock_num = None
    import re
    m = re.search(r"(?:stock|qty|quantit[eé]|restant|left)\D*(\d{1,5})", norm_all)
    if m:
        try:
            stock_num = int(m.group(1))
        except Exception:
            pass

    return price_val, stock_num, status

# ---------- Change detection & logging ----------
def ensure_csv_header():
    if not os.path.exists(CHANGES_CSV):
        os.makedirs(os.path.dirname(CHANGES_CSV), exist_ok=True)
        with open(CHANGES_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp","product_id","field","old_value","new_value","url","detail"])

def log_change(event: ChangeEvent):
    ensure_csv_header()
    with open(CHANGES_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([event.happened_at or datetime.utcnow(), event.product_id, event.field, event.old_value, event.new_value, event.url, event.detail or ""])

def notify(subject: str, body: str):
    # Currently email; extend here for SMS/WhatsApp/etc.
    send_email(subject, body)
    send_whatsapp(f"{subject}\n{body}")

def compare_and_update(db, product: Product, now_price, now_stock, now_status, http_status, raw_hash):
    changed = False
    # Page gone (via status)
    if now_status == "gone" or (http_status and http_status in (404,410)):
        if product.status != "gone":
            ev = ChangeEvent(product_id=product.id, field="page", old_value=product.status, new_value="gone", url=product.url, detail=f"http_status={http_status}")
            db.add(ev); db.flush()
            log_change(ev)
            notify(f"[PAGE GONE] {product.name}", f"La page du produit a disparu: {product.url}\nAncien statut: {product.status}\nHTTP: {http_status}")
            product.status = "gone"; product.stock = 0
            changed = True
        # still create snapshot
        return changed

    # Price change
    if now_price is not None and product.price != now_price:
        ev = ChangeEvent(product_id=product.id, field="price", old_value=str(product.price), new_value=str(now_price), url=product.url)
        db.add(ev); db.flush()
        log_change(ev)
        notify(f"[PRICE CHANGE] {product.name}", f"Prix modifié: {product.price} -> {now_price}\n{product.url}")
        product.price = now_price
        changed = True

    # Stock change to zero or numeric change
    if now_stock is not None and product.stock != now_stock:
        ev = ChangeEvent(product_id=product.id, field="stock", old_value=str(product.stock), new_value=str(now_stock), url=product.url)
        db.add(ev); db.flush()
        log_change(ev)
        if (product.stock is None or product.stock > 0) and now_stock == 0:
            notify(f"[OUT OF STOCK] {product.name}", f"Stock épuisé.\n{product.url}")
        product.stock = now_stock
        changed = True

    # Availability status change
    if product.status != now_status:
        ev = ChangeEvent(product_id=product.id, field="status", old_value=product.status, new_value=now_status, url=product.url)
        db.add(ev); db.flush()
        log_change(ev)
        if now_status == "unavailable":
            notify(f"[UNAVAILABLE] {product.name}", f"Le produit est indisponible.\n{product.url}")
        elif now_status == "available":
            notify(f"[BACK IN STOCK] {product.name}", f"Le produit est de nouveau disponible.\n{product.url}")
        product.status = now_status
        changed = True

    return changed

def run_once():
    Base.metadata.create_all(bind=engine)
    vendors_cfg = load_vendor_config()
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id.asc()).all()
        total = len(products)
        print(f"Checking {total} products...")
        for p in products:
            vcfg = None
            if p.vendor and p.vendor != "auto":
                # find vendor by exact name OR domain
                for v in vendors_cfg.get("vendors", []):
                    if p.vendor in (v.get("name"), v.get("domain")):
                        vcfg = v; break
            else:
                vcfg = pick_vendor(vendors_cfg, p.url)
            # default to static if unknown
            scraper = choose_scraper(vcfg)
            res = scraper.fetch(p.url)

            # Prepare defaults
            price_now = None; stock_now = None; status_now = "unknown"
            http_status = res.status_code
            note = None

            if not res.ok or not res.html:
                status_now = "gone" if (http_status in (404,410)) else "unavailable"
                note = res.error or f"http_status={http_status}"
                raw_h = None
            else:
                soup = scraper.soup(res.html)
                price_now, stock_now, status_now = interpret_fields(vcfg, soup, res.html)
                raw_h = safe_hash_html(res.html)

            # Snapshot
            snap = Snapshot(product_id=p.id, price=price_now, stock=stock_now, status=status_now, http_status=http_status, raw_hash=raw_h, note=note)
            db.add(snap); db.flush()

            # Compare & update product
            changed = compare_and_update(db, p, price_now, stock_now, status_now, http_status, raw_h)
            if changed:
                p.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
        print("ERROR run_once:", e)
        raise
    finally:
        db.close()

def run_daemon(hours: int):
    import schedule, time
    schedule.every(hours).hours.do(run_once)
    print(f"Daemon started. Running every {hours} hour(s). Ctrl+C to stop.")
    run_once()
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")

def main():
    parser = argparse.ArgumentParser(description="Supplier Monitor Bot")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("run-once", help="Exécute une vérification maintenant")

    p_daemon = sub.add_parser("run-daemon", help="Boucle continue avec schedule")
    p_daemon.add_argument("--every-hours", type=int, default=3)

    args = parser.parse_args()
    if args.cmd == "run-once":
        run_once()
    elif args.cmd == "run-daemon":
        run_daemon(args.every_hours)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
