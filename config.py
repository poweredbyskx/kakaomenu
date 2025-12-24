import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

# ❗ Правильный путь: app/static/uploads
UPLOADS_ROOT = BASE_DIR / "app" / "static" / "uploads"

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'cafe.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB для загрузок

    # используем правильный путь
    UPLOADS_ROOT = os.environ.get("UPLOADS_ROOT", str(UPLOADS_ROOT))
    DISH_UPLOAD_SUBDIR = "dishes"













