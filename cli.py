\
from __future__ import annotations
import os, sys, argparse, csv
from urllib.parse import urlparse
from dotenv import load_dotenv
import pandas as pd

from store.db import SessionLocal, Base, engine
from store.models import Product, Snapshot, ChangeEvent

load_dotenv()

def init_db():
    Base.metadata.create_all(bind=engine)

def add_product(name: str, url: str, vendor: str = "auto", price=None, stock=None, status="unknown"):
    db = SessionLocal()
    try:
        p = Product(name=name, url=url, vendor=vendor, price=price, stock=stock, status=status)
        db.add(p); db.commit()
        print(f"Added product id={p.id}: {p.name}")
    except Exception as e:
        db.rollback()
        print("ERROR add:", e)
    finally:
        db.close()

def list_products():
    db = SessionLocal()
    try:
        for p in db.query(Product).order_by(Product.id.asc()).all():
            print(f"{p.id:4d} | {p.name[:40]:40s} | {p.url}")
    finally:
        db.close()

def remove_product(pid: int):
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == pid).first()
        if not p:
            print("Not found")
            return
        db.delete(p); db.commit()
        print("Deleted", pid)
    except Exception as e:
        db.rollback()
        print("ERROR remove:", e)
    finally:
        db.close()

def import_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            add_product(row.get("name") or row.get("Nom", "Sans nom"),
                        row.get("url") or row.get("URL"),
                        vendor=row.get("vendor","auto"),
                        price=float(row["price"]) if row.get("price") else None,
                        stock=int(row["stock"]) if row.get("stock") else None,
                        status=row.get("status","unknown"))

def export_excel(path: str):
    import pandas as pd
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        snaps = db.query(Snapshot).all()
        changes = db.query(ChangeEvent).all()

        df_p = pd.DataFrame([{
            "id": p.id, "name": p.name, "url": p.url, "vendor": p.vendor, "price": p.price, "stock": p.stock, "status": p.status,
            "created_at": p.created_at, "updated_at": p.updated_at
        } for p in products])

        df_s = pd.DataFrame([{
            "id": s.id, "product_id": s.product_id, "fetched_at": s.fetched_at, "price": s.price, "stock": s.stock, "status": s.status, "http_status": s.http_status, "note": s.note
        } for s in snaps])

        df_c = pd.DataFrame([{
            "id": c.id, "product_id": c.product_id, "happened_at": c.happened_at, "field": c.field, "old_value": c.old_value, "new_value": c.new_value, "url": c.url, "detail": c.detail
        } for c in changes])

        with pd.ExcelWriter(path) as writer:
            df_p.to_excel(writer, index=False, sheet_name="products")
            df_s.to_excel(writer, index=False, sheet_name="snapshots")
            df_c.to_excel(writer, index=False, sheet_name="changes")
        print("Exported:", path)
    finally:
        db.close()

def main():
    init_db()
    ap = argparse.ArgumentParser(description="CLI pour gérer la base Produits & exports")
    sub = ap.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--url", required=True)
    p_add.add_argument("--vendor", default="auto")

    sub.add_parser("list")
    p_rm = sub.add_parser("remove")
    p_rm.add_argument("--id", type=int, required=True)

    p_import = sub.add_parser("import-csv")
    p_import.add_argument("path")

    p_export = sub.add_parser("export-excel")
    p_export.add_argument("path")

    args = ap.parse_args()
    if args.cmd == "add":
        add_product(args.name, args.url, args.vendor)
    elif args.cmd == "list":
        list_products()
    elif args.cmd == "remove":
        remove_product(args.id)
    elif args.cmd == "import-csv":
        import_csv(args.path)
    elif args.cmd == "export-excel":
        export_excel(args.path)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
