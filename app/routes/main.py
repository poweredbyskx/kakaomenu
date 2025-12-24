from flask import (
    jsonify,
    render_template,
    request,
    url_for,
)

from . import main_bp
from ..models import Category, Dish


@main_bp.route("/")
def index():
    """Главная страница с меню."""
    return render_template("menu.html")


@main_bp.get("/api/categories")
def get_categories():
    """Получить все категории из БД."""
    categories = Category.query.order_by(Category.order_num, Category.id).all()
    return jsonify(
        [
            {
                "id": c.id,
                "name": c.name,
            }
            for c in categories
        ]
    )


@main_bp.get("/api/dishes")
def get_dishes():
    """Получить блюда, опционально по категории."""
    category_id = request.args.get("category_id", type=int)

    query = Dish.query
    if category_id:
        query = query.filter(Dish.category_id == category_id)

    dishes = query.order_by(Dish.id).all()

    result = []
    for d in dishes:
        image_url = ""
        if d.image_path:
            # Нормализуем путь: заменяем обратные слеши на прямые для URL
            normalized_path = d.image_path.replace("\\", "/")
            image_url = url_for("static", filename=normalized_path)
        result.append({
            "id": d.id,
            "name": d.name,
            "description": d.description or "",
            "price": d.price or "—",
            "image_path": image_url,
            "category_id": d.category_id,
        })
    return jsonify(result)


# Images are now served directly from static folder via Flask's static route
# This route is kept for backward compatibility but redirects to static
@main_bp.route("/uploads/<path:filename>")
def serve_upload(filename: str):
    """Редирект на статические файлы (для обратной совместимости)."""
    from flask import redirect
    return redirect(url_for("static", filename=f"uploads/{filename}"), code=301)
