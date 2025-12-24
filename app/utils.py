import os
import secrets
from pathlib import Path

from flask import current_app
from PIL import Image


def _ensure_upload_folder(category_name: str | None = None) -> Path:
    """Создать папку для загрузки, при необходимости с подпапкой категории."""
    upload_root = Path(current_app.config["UPLOADS_ROOT"])
    upload_folder = upload_root / current_app.config["DISH_UPLOAD_SUBDIR"]
    
    # Если указано имя категории, создаём подпапку с этим именем
    if category_name:
        upload_folder = upload_folder / category_name
    
    upload_folder.mkdir(parents=True, exist_ok=True)
    return upload_folder


def save_dish_image(file_storage, category_name: str | None = None) -> str:
    """
    Сохранить и сжать изображение блюда.

    Args:
        file_storage: FileStorage объект из request.files
        category_name: Имя категории для создания подпапки (например, "Кофе")

    Возвращает относительный путь от static folder, например:
        uploads/dishes/Кофе/abc123.jpg (если category_name указан)
        uploads/dishes/abc123.jpg (если category_name не указан)
    Этот путь используется с url_for('static', filename=...)
    """
    if not file_storage:
        return ""

    upload_folder = _ensure_upload_folder(category_name)

    # Генерируем безопасное имя файла
    ext = os.path.splitext(file_storage.filename)[1].lower() or ".jpg"
    filename = secrets.token_hex(16) + ext
    filepath = upload_folder / filename

    # Сохраняем и сжимаем
    image = Image.open(file_storage)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((1600, 1600))
    image.save(filepath, optimize=True, quality=80)

    # Путь относительно static folder для использования с url_for('static', filename=...)
    base_path = f"uploads/{current_app.config['DISH_UPLOAD_SUBDIR']}"
    if category_name:
        return f"{base_path}/{category_name}/{filename}"
    return f"{base_path}/{filename}"


def delete_image(image_path: str | None) -> None:
    """
    Удалить файл изображения с диска.

    Args:
        image_path: Относительный путь от static folder (например, "uploads/dishes/Кофе/abc123.jpg")
    """
    if not image_path:
        return
    
    try:
        static_folder = Path(current_app.static_folder)
        file_path = static_folder / image_path
        
        # Проверяем, что путь находится внутри static folder (безопасность)
        try:
            file_path.resolve().relative_to(static_folder.resolve())
        except ValueError:
            # Путь находится вне static folder - не удаляем
            return
        
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception:
        # Игнорируем ошибки при удалении (файл может уже не существовать)
        pass
