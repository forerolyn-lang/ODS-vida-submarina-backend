import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── General ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "cambia-este-secreto-en-produccion")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # ── Base de datos ─────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///oceanlearn.db"          # SQLite para desarrollo local
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False                 # True para ver queries en consola

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secreto-cambiame")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=int(os.getenv("JWT_ACCESS_HOURS",  "8")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS",  "30")))

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    # ── Subida de archivos ────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024          # 10 MB máximo por archivo
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

    # ── Paginación ────────────────────────────────────────────────────────────
    PAGE_SIZE_DEFAULT = 20
    PAGE_SIZE_MAX     = 100


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")   # PostgreSQL en prod


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
