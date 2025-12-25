import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
from pathlib import Path

import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, static_folder="static", template_folder="templates")

    # Базовая конфигурация
    from config import Config

    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(Config)
        app.config.update(test_config)

    # Убедимся, что папки instance и uploads существуют
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    uploads_root = Path(app.config["UPLOADS_ROOT"])
    uploads_root.mkdir(parents=True, exist_ok=True)
    (uploads_root / app.config["DISH_UPLOAD_SUBDIR"]).mkdir(parents=True, exist_ok=True)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "error"

    # Регистрация blueprints
    from .routes.main import main_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Модели импортируются для Alembic
    from . import models  # noqa: F401

    # Инициализация единственного администратора (Boss/kakao)
    init_single_admin(app)

    register_cli_commands(app)

    return app


def init_single_admin(app: Flask) -> None:
    """Инициализировать единственного администратора: username=Boss, password=kakao."""
    with app.app_context():
        from .models import AdminUser

        # Удалить всех других администраторов (не Boss)
        other_admins = AdminUser.query.filter(AdminUser.username != "Boss").all()
        for admin in other_admins:
            db.session.delete(admin)

        # Создать Boss администратора, если не существует
        boss_admin = AdminUser.query.filter_by(username="Boss").first()
        if not boss_admin:
            boss_admin = AdminUser(username="Boss")
            boss_admin.set_password("kakao")
            db.session.add(boss_admin)
            db.session.commit()
        else:
            db.session.commit()


def register_cli_commands(app: Flask) -> None:
    from .models import AdminUser, Category, Dish
    from .seed_data import CATEGORY_FIXTURES, DISH_FIXTURES

    @app.cli.command("seed-db")
    @click.option("--force", is_flag=True, help="Удалить данные перед наполнением")
    def seed_db(force: bool) -> None:
        """Заполнить базу начальными категориями и блюдами."""
        if force:
            Dish.query.delete()
            Category.query.delete()
            db.session.commit()

        if Category.query.count() > 0 and not force:
            click.secho("[!] Категории уже заполнены — пропускаю (используйте --force).", fg="yellow")
            return

        categories_map: dict[str, Category] = {}
        for data in CATEGORY_FIXTURES:
            category = Category(name=data["name"], order_num=data.get("order_num", 0))
            db.session.add(category)
            categories_map[category.name] = category
        db.session.flush()

        for data in DISH_FIXTURES:
            category = categories_map.get(data["category"])
            if not category:
                continue
            dish = Dish(
                name=data["name"],
                description=data.get("description", ""),
                price=data.get("price", "—"),
                image_path=data.get("image_path", ""),
                category=category,
            )
            db.session.add(dish)

        db.session.commit()
        click.secho("[OK] Данные успешно загружены.", fg="green")


    @app.cli.command("import-dishes")
    @click.option("--update", is_flag=True, help="Обновить пути к изображениям для существующих блюд")
    def import_dishes(update: bool) -> None:
        """Импортировать все блюда из app/static/uploads/dishes/ (имена файлов = названия блюд)."""
        from pathlib import Path

        dishes_dir = Path(app.static_folder) / "uploads" / "dishes"
        
        if not dishes_dir.exists():
            click.secho(f"[!] Папка {dishes_dir} не найдена.", fg="red")
            return

        # Get or create categories from folder names
        category_map = {}
        for cat_folder in sorted(dishes_dir.iterdir()):
            if not cat_folder.is_dir():
                continue

            category_name = cat_folder.name
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                max_order = db.session.query(db.func.max(Category.order_num)).scalar() or 0
                category = Category(name=category_name, order_num=max_order + 1)
                db.session.add(category)
                db.session.flush()
                click.echo(f"Создана категория: {category_name}")
            category_map[category_name] = category

        db.session.commit()

        # Import dishes from images
        total_imported = 0
        total_updated = 0
        total_existing = 0

        for cat_folder in sorted(dishes_dir.iterdir()):
            if not cat_folder.is_dir():
                continue

            category = category_map[cat_folder.name]

            for image_file in sorted(cat_folder.glob("*.jpg")):
                dish_name = image_file.stem
                image_path = f"uploads/dishes/{cat_folder.name}/{image_file.name}"

                existing_dish = Dish.query.filter_by(
                    name=dish_name, category_id=category.id
                ).first()

                if existing_dish:
                    total_existing += 1
                    if update and existing_dish.image_path != image_path:
                        existing_dish.image_path = image_path
                        total_updated += 1
                else:
                    dish = Dish(
                        name=dish_name,
                        description="",
                        price="—",
                        image_path=image_path,
                        category=category,
                    )
                    db.session.add(dish)
                    total_imported += 1

        db.session.commit()
        click.secho(
            f"[OK] Импорт завершен: новых {total_imported}, "
            f"обновлено {total_updated}, существующих {total_existing}, "
            f"всего блюд {Dish.query.count()}",
            fg="green",
        )



