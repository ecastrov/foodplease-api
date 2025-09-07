from __future__ import annotations

import os
from flask import Flask
from flask_cors import CORS

from .database import init_engine_and_session, init_db_and_seed
from .routes import register_blueprints
from .utils import ok, now_utc

def create_app() -> Flask:
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
    app.config["ACCESS_TOKEN_EXPIRES_MIN"] = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "120"))
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///rappi_like.db")

    # CORS (Flutter-friendly)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # DB engine & session factory
    init_engine_and_session(app.config["DATABASE_URL"])

    # Create tables + seed admin if missing
    init_db_and_seed()

    # Blueprints (auth, products, orders)
    register_blueprints(app)

    # Root & health endpoints
    @app.get("/")
    def root():
        return ok({"service": "rappi-like-api", "version": 1})

    @app.get("/api/health")
    def health():
        return ok({"status": "ok", "time": now_utc().isoformat()})

    return app