from __future__ import annotations
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    vendor = Column(String(255), nullable=True)  # 'auto' pour auto-détection via domaine
    price = Column(Float, nullable=True)        # dernier prix connu
    stock = Column(Integer, nullable=True)      # dernier stock connu (None si inconnu)
    status = Column(String(50), default="unknown")  # available/unavailable/gone/unknown
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    snapshots = relationship("Snapshot", back_populates="product", cascade="all, delete-orphan")

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    price = Column(Float, nullable=True)
    stock = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False)  # available/unavailable/gone/unknown
    http_status = Column(Integer, nullable=True)
    raw_hash = Column(String(64), nullable=True)  # hash du HTML nettoyé (optionnel)
    note = Column(Text, nullable=True)

    product = relationship("Product", back_populates="snapshots")

class ChangeEvent(Base):
    __tablename__ = "change_events"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    happened_at = Column(DateTime(timezone=True), server_default=func.now())
    field = Column(String(50), nullable=False)  # price|stock|status|page
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    url = Column(Text, nullable=False)
    detail = Column(Text, nullable=True)
