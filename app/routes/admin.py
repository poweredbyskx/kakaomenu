# app/routes/admin.py

from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from . import admin_bp
from .. import csrf, db
from ..forms import LoginForm
from ..models import AdminUser, Category, Dish
from ..utils import delete_image, save_dish_image


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("admin.dashboard"))
        flash("Неверный логин или пароль", "error")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    categories = Category.query.order_by(Category.order_num, Category.id).all()
    return render_template("admin/dashboard.html", categories=categories)


@admin_bp.post("/api/dish")
@csrf.exempt
@login_required
def add_dish():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", "").strip() or "—"
    category_id = request.form.get("category_id", type=int)

    if not name or not category_id:
        return jsonify({"error": "Название и категория обязательны"}), 400

    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"error": "Категория не найдена"}), 400

    image_file = request.files.get("image")
    image_path = save_dish_image(image_file, category.name) if image_file else ""

    dish = Dish(
        name=name,
        description=description,
        price=price,
        category=category,
        image_path=image_path,
    )
    db.session.add(dish)
    db.session.commit()

    return jsonify({"id": dish.id, "name": dish.name}), 201


@admin_bp.get("/api/dish/<int:dish_id>")
@csrf.exempt
@login_required
def get_dish(dish_id: int):
    """Получить данные одного блюда для редактирования (для фронтенда)."""
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return jsonify({"error": "Блюдо не найдено"}), 404

    image_url = ""
    if dish.image_path:
        # Нормализуем слеши для Windows/Linux совместимости
        normalized_path = dish.image_path.replace("\\", "/")
        image_url = url_for("static", filename=normalized_path, _external=True)  # _external=True для полного URL (удобно для JS)

    return jsonify({
        "id": dish.id,
        "name": dish.name,
        "description": dish.description or "",
        "price": dish.price or "—",
        "category_id": dish.category_id,
        "image_url": image_url,  # лучше назвать image_url, а не image_path
    })


@admin_bp.put("/api/dish/<int:dish_id>")
@csrf.exempt
@login_required
def update_dish(dish_id: int):
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return jsonify({"error": "Блюдо не найдено"}), 404

    # Поддержка JSON и form-data
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict()

    # Текстовые поля
    if "name" in data:
        dish.name = str(data["name"]).strip()
    if "description" in data:
        dish.description = str(data["description"]).strip()
    if "price" in data:
        dish.price = str(data["price"]).strip() or "—"

    new_category = None
    if "category_id" in data:
        try:
            category_id = int(data["category_id"])
        except (ValueError, TypeError):
            return jsonify({"error": "Неверный category_id"}), 400
        new_category = db.session.get(Category, category_id)
        if not new_category:
            return jsonify({"error": "Категория не найдена"}), 400
        dish.category = new_category

    # Новое изображение
    image_file = request.files.get("image")
    if image_file and image_file.filename:  # проверяем, что файл реально загружен
        # Удаляем старое
        if dish.image_path:
            delete_image(dish.image_path)

        # Сохраняем новое в папку актуальной категории
        target_category = new_category or dish.category
        dish.image_path = save_dish_image(image_file, target_category.name)

    db.session.commit()
    return jsonify({"id": dish.id, "name": dish.name}), 200


@admin_bp.delete("/api/dish/<int:dish_id>")
@csrf.exempt
@login_required
def delete_dish(dish_id: int):
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return jsonify({"error": "Блюдо не найдено"}), 404

    if dish.image_path:
        delete_image(dish.image_path)

    db.session.delete(dish)
    db.session.commit()

    return jsonify({"message": "Блюдо удалено"}), 200
