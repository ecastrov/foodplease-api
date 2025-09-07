from __future__ import annotations

from flask import Blueprint, request

from ..database import get_session
from ..models import Product, Order, OrderItem
from ..utils import ok, error_response, get_pagination, order_to_dict, token_required

bp = Blueprint("orders", __name__)

@bp.get("")
@token_required
def list_orders():
    page, per_page = get_pagination()
    status = request.args.get("status")

    with get_session() as s:
        query = s.query(Order)
        if status:
            query = query.filter(Order.status == status)
        total = query.count()
        rows = query.order_by(Order.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return ok([order_to_dict(o) for o in rows], meta={"page": page, "per_page": per_page, "total": total})

@bp.post("")
@token_required
def create_order():
    body = request.get_json(silent=True) or {}
    items = body.get("items") or []  # [{product_id, quantity}]
    address = body.get("address")
    meta = body.get("meta") or {}

    if not items:
        return error_response("Order must include at least one item", 400)

    with get_session() as s:
        user_payload = getattr(request, "user", {})
        user_id = int(user_payload.get("sub"))
        order = Order(user_id=user_id, address=address, meta=meta, status="pending")

        total = 0.0
        for item in items:
            pid = int(item.get("product_id"))
            qty = int(item.get("quantity", 1))
            if qty <= 0:
                return error_response("quantity must be > 0", 400)
            product = s.get(Product, pid)
            if not product or not product.is_active:
                return error_response(f"Product {pid} not available", 400)
            if product.stock < qty:
                return error_response(f"Insufficient stock for product {pid}", 400)
            unit_price = float(product.price)
            subtotal = unit_price * qty
            product.stock -= qty
            order.items.append(OrderItem(product_id=pid, quantity=qty, unit_price=unit_price, subtotal=subtotal))
            total += subtotal

        order.total_amount = round(total, 2)
        s.add(order)
        s.commit()
        s.refresh(order)
        return ok(order_to_dict(order), status=201)

@bp.get("/<int:oid>")
@token_required
def get_order(oid: int):
    with get_session() as s:
        o = s.get(Order, oid)
        if not o:
            return error_response("Order not found", 404)
        return ok(order_to_dict(o))

@bp.patch("/<int:oid>")
@token_required
def update_order(oid: int):
    body = request.get_json(silent=True) or {}
    with get_session() as s:
        o = s.get(Order, oid)
        if not o:
            return error_response("Order not found", 404)
        if "status" in body:
            o.status = (body.get("status") or o.status).strip()
        if "address" in body:
            o.address = body.get("address")
        if "meta" in body and isinstance(body.get("meta"), dict):
            o.meta = body.get("meta")
        s.commit()
        s.refresh(o)
        return ok(order_to_dict(o))

@bp.delete("/<int:oid>")
@token_required
def delete_order(oid: int):
    if getattr(request, "user", {}).get("role") != "admin":
        return error_response("Forbidden", 403)
    with get_session() as s:
        o = s.get(Order, oid)
        if not o:
            return error_response("Order not found", 404)
        # Restore stock when deleting an order
        for it in o.items:
            prod = s.get(Product, it.product_id)
            if prod:
                prod.stock += it.quantity
        s.delete(o)
        s.commit()
        return ok({"deleted": True})