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
@csrf.exempt  # используем fetch в JS без CSRF токена
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
    """Получить данные одного блюда для редактирования."""
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return jsonify({"error": "Блюдо не найдено"}), 404
    
    from flask import url_for
    image_url = ""
    if dish.image_path:
        normalized_path = dish.image_path.replace("\\", "/")
        image_url = url_for("static", filename=normalized_path)
    
    return jsonify({
        "id": dish.id,
        "name": dish.name,
        "description": dish.description or "",
        "price": dish.price or "—",
        "category_id": dish.category_id,
        "image_path": image_url,
    })


@admin_bp.put("/api/dish/<int:dish_id>")
@csrf.exempt
@login_required
def update_dish(dish_id: int):
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return jsonify({"error": "Блюдо не найдено"}), 404

    # Поддерживаем как JSON, так и multipart/form-data
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict()

    # Обновляем текстовые поля
    if "name" in data:
        dish.name = data["name"].strip() if isinstance(data["name"], str) else str(data["name"]).strip()
    if "description" in data:
        dish.description = data["description"].strip() if isinstance(data["description"], str) else str(data["description"]).strip()
    if "price" in data:
        dish.price = (data["price"].strip() if isinstance(data["price"], str) else str(data["price"]).strip()) or "—"
    
    # Обновляем категорию (если изменена)
    new_category = None
    if "category_id" in data:
        category_id = int(data["category_id"]) if isinstance(data["category_id"], str) else data["category_id"]
        new_category = db.session.get(Category, category_id)
        if not new_category:
            return jsonify({"error": "Категория не найдена"}), 400
        dish.category = new_category
    
    # Обрабатываем загрузку нового изображения
    image_file = request.files.get("image")
    if image_file:
        # Удаляем старое изображение, если оно было
        if dish.image_path:
            delete_image(dish.image_path)
        
        # Определяем категорию для сохранения (новая или текущая)
        target_category = new_category if new_category else dish.category
        dish.image_path = save_dish_image(image_file, target_category.name)

    db.session.commit()
    return jsonify({"id": dish.id, "name": dish.name})


@admin_bp.delete("/api/dish/<int:dish_id>")
@csrf.exempt
@login_required
def delete_dish(dish_id: int):
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return jsonify({"error": "Блюдо не найдено"}), 404

    # Удаляем файл изображения, если он существует
    if dish.image_path:
        delete_image(dish.image_path)

    db.session.delete(dish)
    db.session.commit()

    return jsonify({"message": "Блюдо удалено"}), 200



