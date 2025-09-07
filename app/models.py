from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy import (
    JSON, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1=True,0=False
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    items: Mapped[List["OrderItem"]] = relationship(back_populates="product")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    address: Mapped[Optional[str]] = mapped_column(String(255))
    meta: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_unit_price_nonneg"),
    )

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="items")