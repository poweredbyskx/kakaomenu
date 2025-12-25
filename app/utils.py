# app/utils.py

import os
import secrets
from pathlib import Path

from flask import current_app
from PIL import Image


def _ensure_upload_folder(category_name: str | None = None) -> Path:
    """
    Создаёт и возвращает путь к папке для загрузки.
    Учитывает возможный Volume на Render/Railway.
    """
    upload_root = Path(current_app.config["UPLOADS_ROOT"])
    upload_folder = upload_root / current_app.config["DISH_UPLOAD_SUBDIR"]

    if category_name:
        # Очищаем имя категории от потенциально опасных символов
        safe_category = "".join(c for c in category_name if c.isalnum() or c in " -_()")
        upload_folder = upload_folder / safe_category.strip()

    upload_folder.mkdir(parents=True, exist_ok=True)
    return upload_folder


def save_dish_image(file_storage, category_name: str | None = None) -> str:
    """
    Сохраняет и сжимает фото блюда.
    Возвращает относительный путь от static (для url_for('static', ...)).
    """
    if not file_storage or not file_storage.filename:
        return ""

    upload_folder = _ensure_upload_folder(category_name)

    # Безопасное случайное имя
    ext = os.path.splitext(file_storage.filename)[1].lower() or ".jpg"
    filename = secrets.token_hex(16) + ext
    filepath = upload_folder / filename

    # Сжатие через Pillow
    image = Image.open(file_storage)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((1600, 1600))
    image.save(filepath, optimize=True, quality=80)

    # Относительный путь для шаблонов
    base = f"uploads/{current_app.config['DISH_UPLOAD_SUBDIR']}"
    if category_name:
        safe_category = "".join(c for c in category_name if c.isalnum() or c in " -_()").strip()
        return f"{base}/{safe_category}/{filename}"
    return f"{base}/{filename}"


def delete_image(image_path: str | None) -> None:
    """
    Безопасно удаляет файл изображения по относительному пути от static.
    """
    if not image_path:
        return

    try:
        # Полный путь от корня static
        static_folder = Path(current_app.static_folder)
        file_path = (static_folder / image_path.lstrip("/")).resolve()

        # Защита от выхода за пределы static (path traversal attack)
        static_folder_resolved = static_folder.resolve()
        if not file_path.is_file() or not str(file_path).startswith(str(static_folder_resolved)):
            return

        file_path.unlink()
    except Exception:
        # Тихо игнорируем ошибки (файл может быть уже удалён или недоступен)
        pass