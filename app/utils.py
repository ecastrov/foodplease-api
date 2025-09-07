from __future__ import annotations

import datetime as dt
import os
from typing import Any, Callable, Optional, Tuple

import jwt
from flask import jsonify, request, current_app
from passlib.hash import bcrypt

from .database import get_session
from .models import User

# ---------- time ----------
def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)

# ---------- responses ----------
def ok(data: Any, meta: Optional[dict] = None, status: int = 200):
    payload = {"data": data}
    if meta:
        payload["meta"] = meta
    return jsonify(payload), status

def error_response(message: str, status: int = 400, code: Optional[str] = None):
    return jsonify({"error": {"message": message, "code": code, "status": status}}), status

def get_pagination() -> Tuple[int, int]:
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError:
        page, per_page = 1, 20
    return page, per_page

# ---------- auth / jwt ----------
def _secret_key() -> str:
    return current_app.config.get("SECRET_KEY") or os.getenv("SECRET_KEY", "change-me")

def _expires_minutes() -> int:
    return int(current_app.config.get("ACCESS_TOKEN_EXPIRES_MIN", 120))

def make_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": int(now_utc().timestamp()),
        "exp": int((now_utc() + dt.timedelta(minutes=_expires_minutes())).timestamp()),
    }
    return jwt.encode(payload, _secret_key(), algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret_key(), algorithms=["HS256"])

def token_required(fn: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("Missing or invalid Authorization header", 401)
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            request.user = payload  # type: ignore[attr-defined]
        except jwt.ExpiredSignatureError:
            return error_response("Token expired", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid token", 401)
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# ---------- serializers ----------
from .models import Product, OrderItem, Order

def product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "is_active": bool(p.is_active),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }

def order_item_to_dict(oi: OrderItem) -> dict:
    return {
        "id": oi.id,
        "product": product_to_dict(oi.product) if oi.product else {"id": oi.product_id},
        "quantity": oi.quantity,
        "unit_price": oi.unit_price,
        "subtotal": oi.subtotal,
    }

def order_to_dict(o: Order) -> dict:
    return {
        "id": o.id,
        "status": o.status,
        "total_amount": o.total_amount,
        "address": o.address,
        "meta": o.meta or {},
        "user": {"id": o.user_id},
        "items": [order_item_to_dict(i) for i in o.items],
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }