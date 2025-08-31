
import os, sys, time
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

from store.db import SessionLocal, Base, engine
from store.models import Product, Snapshot, ChangeEvent

Base.metadata.create_all(bind=engine)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from store.db import SessionLocal, Base, engine
from store.models import Product, Snapshot, ChangeEvent
import monitor as monitor_mod

st.set_page_config(
    page_title="Supplier Monitor — Dashboard",
    page_icon="🧭",
    layout="wide",
)

st.markdown("""
<style>
:root { --glass-bg: rgba(20, 24, 38, 0.55); --glass-border: rgba(255,255,255,0.12); }
.stApp { background: radial-gradient(60% 120% at 20% 10%, #0b132b 0%, #1b2a49 35%, #020817 100%) fixed; color: #e2e8f0; }
.block-container {padding-top: 2rem;}
.css-1dp5vir, .css-1r6slb0, .css-1v0mbdj, .stMarkdown, .stDataFrame, .stPlotlyChart, .stNumberInput, .stTextInput, .stSelectbox {
  backdrop-filter: blur(10px); background: var(--glass-bg) !important; border: 1px solid var(--glass-border); border-radius: 16px !important;
}
.stButton>button { border-radius: 999px; padding: 0.6rem 1rem; border: 1px solid rgba(255,255,255,0.15);
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(0,0,0,0.2)); color: #f8fafc; }
.stButton>button:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
thead tr th { background: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)

st.title("🧭 Supplier Monitor — Dashboard")

def df_products(session):
    rows = session.query(Product).order_by(Product.id.asc()).all()
    return pd.DataFrame([{
        "id": p.id, "name": p.name, "url": p.url, "vendor": p.vendor,
        "price": p.price, "stock": p.stock, "status": p.status,
        "created_at": p.created_at, "updated_at": p.updated_at
    } for p in rows])

def df_snapshots(session, limit=500):
    rows = session.query(Snapshot).order_by(Snapshot.id.desc()).limit(limit).all()
    return pd.DataFrame([{
        "id": s.id, "product_id": s.product_id, "fetched_at": s.fetched_at,
        "price": s.price, "stock": s.stock, "status": s.status,
        "http_status": s.http_status, "note": s.note
    } for s in rows])

def df_changes(session, limit=500):
    rows = session.query(ChangeEvent).order_by(ChangeEvent.id.desc()).limit(limit).all()
    return pd.DataFrame([{
        "id": c.id, "when": c.happened_at, "product_id": c.product_id, "field": c.field,
        "old": c.old_value, "new": c.new_value, "url": c.url, "detail": c.detail
    } for c in rows])

with st.sidebar:
    st.header("Actions")
    if st.button("🔁 Lancer une vérification maintenant", use_container_width=True):
        with st.spinner("Exécution du bot (run_once)..."):
            monitor_mod.run_once()
        st.success("Vérification terminée. Les données ont été mises à jour.")
        st.rerun()

    st.divider()
    st.header("Outils")
    if st.button("📧 Envoyer un email de test", use_container_width=True):
        from notifiers.email_notifier import send_email
        ok = send_email("[TEST] Supplier Monitor", "Test email depuis le Dashboard.")
        st.toast("Email envoyé ✅" if ok else "Email en DRY-RUN (config manquante) ⚠️", icon="📧")

    if st.button("💬 Envoyer un WhatsApp de test", use_container_width=True):
        try:
            from notifiers.twilio_notifier import send_whatsapp
            ok = send_whatsapp("✅ Test WhatsApp depuis le Dashboard.")
            st.toast("WhatsApp envoyé ✅" if ok else "WhatsApp en DRY-RUN (config manquante) ⚠️", icon="💬")
        except Exception as e:
            st.error(f"Erreur import Twilio: {e}")

    st.divider()
    st.caption("Astuce : pour l'exécution planifiée, lance `monitor.py run-daemon` dans un autre terminal.")

session = SessionLocal()
dfp = df_products(session)
total_p = len(dfp)
available = int((dfp["status"] == "available").sum()) if total_p else 0
unavailable = int((dfp["status"] == "unavailable").sum()) if total_p else 0
gone = int((dfp["status"] == "gone").sum()) if total_p else 0

c1,c2,c3,c4 = st.columns(4)
c1.metric("Produits", f"{total_p}")
c2.metric("Disponibles", f"{available}")
c3.metric("Indisponibles", f"{unavailable}")
c4.metric("Page disparue", f"{gone}")

st.subheader("📦 Produits")
with st.expander("Afficher / filtrer les produits", expanded=True):
    if not dfp.empty:
        q = st.text_input("Filtre", placeholder="Nom ou URL...")
        view = dfp.copy()
        if q:
            ql = q.lower()
            view = view[view["name"].str.lower().str.contains(ql) | view["url"].str.lower().str.contains(ql)]
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun produit. Utilise la CLI ou ajoute via CSV.")

st.subheader("🕒 Derniers changements")
dfc = df_changes(session, limit=300)
if dfc.empty:
    st.info("Pas encore de changements détectés.")
else:
    st.dataframe(dfc, use_container_width=True, hide_index=True)

st.subheader("📈 Historique & Analyse")
colA, colB = st.columns([1,2])
with colA:
    product_options = {f"[{row.id}] {row.name}": int(row.id) for row in dfp.itertuples()} if not dfp.empty else {}
    selected = st.selectbox("Choisir un produit", list(product_options.keys())) if product_options else None
with colB:
    if selected:
        pid = product_options[selected]
        dfs = df_snapshots(session, limit=2000)
        hist = dfs[dfs["product_id"]==pid].sort_values("fetched_at")
        if hist.empty:
            st.warning("Pas encore d'historique pour ce produit.")
        else:
            import plotly.express as px
            p_hist = hist.dropna(subset=["price"])
            if not p_hist.empty:
                fig = px.line(p_hist, x="fetched_at", y="price", markers=True, title="Évolution du prix")
                st.plotly_chart(fig, use_container_width=True)
            s_hist = hist.dropna(subset=["stock"])
            if not s_hist.empty:
                fig2 = px.step(s_hist, x="fetched_at", y="stock", title="Évolution du stock")
                st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(hist[["fetched_at","price","stock","status","http_status","note"]], use_container_width=True, hide_index=True)

session.close()
