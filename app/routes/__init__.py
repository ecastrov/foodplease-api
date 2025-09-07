from __future__ import annotations

from flask import Flask
from .auth import bp as auth_bp
from .products import bp as products_bp
from .orders import bp as orders_bp

def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")