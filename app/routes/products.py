from __future__ import annotations

from flask import Blueprint, request

from ..database import get_session
from ..models import Product
from ..utils import ok, error_response, get_pagination, product_to_dict, token_required

bp = Blueprint("products", __name__)

@bp.get("")
@token_required
def list_products():
    q = request.args.get("q", "").strip()
    only_active = request.args.get("only_active") in ("1", "true", "True")
    page, per_page = get_pagination()

    with get_session() as s:
        query = s.query(Product)
        if q:
            like = f"%{q}%"
            query = query.filter(Product.name.ilike(like))
        if only_active:
            query = query.filter(Product.is_active == 1)
        total = query.count()
        rows = query.order_by(Product.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return ok([product_to_dict(p) for p in rows], meta={"page": page, "per_page": per_page, "total": total})

@bp.post("")
@token_required
def create_product():
    if getattr(request, "user", {}).get("role") != "admin":
        return error_response("Forbidden", 403)

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    price = body.get("price")
    stock = int(body.get("stock") or 0)
    description = body.get("description")
    is_active = 1 if (body.get("is_active", True)) else 0

    if not name:
        return error_response("name is required", 400)
    try:
        price = float(price)
        if price < 0:
            raise ValueError
    except Exception:
        return error_response("price must be a non-negative number", 400)

    with get_session() as s:
        p = Product(name=name, description=description, price=price, stock=stock, is_active=is_active)
        s.add(p)
        s.commit()
        s.refresh(p)
        return ok(product_to_dict(p), status=201)

@bp.get("/<int:pid>")
@token_required
def get_product(pid: int):
    with get_session() as s:
        p = s.get(Product, pid)
        if not p:
            return error_response("Product not found", 404)
        return ok(product_to_dict(p))

@bp.put("/<int:pid>")
@bp.patch("/<int:pid>")
@token_required
def update_product(pid: int):
    if getattr(request, "user", {}).get("role") != "admin":
        return error_response("Forbidden", 403)

    body = request.get_json(silent=True) or {}
    with get_session() as s:
        p = s.get(Product, pid)
        if not p:
            return error_response("Product not found", 404)
        if "name" in body:
            p.name = (body.get("name") or p.name).strip()
        if "description" in body:
            p.description = body.get("description")
        if "price" in body:
            try:
                price = float(body.get("price"))
                if price < 0:
                    raise ValueError
                p.price = price
            except Exception:
                return error_response("price must be a non-negative number", 400)
        if "stock" in body:
            p.stock = int(body.get("stock") or 0)
        if "is_active" in body:
            p.is_active = 1 if body.get("is_active") else 0
        s.commit()
        s.refresh(p)
        return ok(product_to_dict(p))

@bp.delete("/<int:pid>")
@token_required
def delete_product(pid: int):
    if getattr(request, "user", {}).get("role") != "admin":
        return error_response("Forbidden", 403)
    with get_session() as s:
        p = s.get(Product, pid)
        if not p:
            return error_response("Product not found", 404)
        s.delete(p)
        s.commit()
        return ok({"deleted": True})