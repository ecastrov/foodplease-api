from __future__ import annotations

from flask import Blueprint, request
from passlib.hash import bcrypt

from ..database import get_session
from ..models import User
from ..utils import ok, error_response, make_token, token_required

bp = Blueprint("auth", __name__)

@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not email or not password:
        return error_response("Email and password are required", 400)

    with get_session() as s:
        user = s.query(User).filter_by(email=email).first()
        if not user or not bcrypt.verify(password, user.password_hash):
            return error_response("Invalid credentials", 401)
        token = make_token(user)
        return ok({"access_token": token, "token_type": "Bearer"})

@bp.post("/register")
@token_required
def register():
    # Only admins can register new users in this demo
    if getattr(request, "user", {}).get("role") != "admin":
        return error_response("Forbidden", 403)

    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    role = (body.get("role") or "customer").strip()

    if not email or not password:
        return error_response("Email and password are required", 400)

    with get_session() as s:
        if s.query(User).filter_by(email=email).first():
            return error_response("Email already registered", 409)
        user = User(email=email, password_hash=bcrypt.hash(password), role=role)
        s.add(user)
        s.commit()
        return ok({"id": user.id, "email": user.email, "role": user.role}, status=201)