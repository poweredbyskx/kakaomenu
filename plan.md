# План разработки сайта-меню кофейни «Какао»

## 1. Технологии

### Frontend
- HTML5 + Jinja2
- Чистый CSS3 (никаких Bootstrap/Tailwind)
- Vanilla JavaScript (только лёгкие эффекты)

### Backend
- Python 3.11+
- Flask 3.x
- Flask-SQLAlchemy + Flask-Migrate
- Flask-Login (простейшая аутентификация)
- WTForms + Flask-WTF

### База данных
- SQLite (на старте и для продакшена до ~500 блюд)
- Хранение только путей к фото

### Хранилище файлов
- Папка `/uploads` в корне проекта (вне static!, в .gitignore)
- Фото блюд сохраняются в `/uploads/dishes/…`

### Развёртывание
- Render / Railway / Fly.io (бесплатный план)
- Позже — любой VPS

---

## 2. Принципы разработки (незыблемые)

- KISS — максимально просто
- Никакого овер-инжиниринга
- Минимум зависимостей
- Чистый, читаемый код, который я смогу поддерживать сам через 5 лет
- Всё, что можно сделать в 50 строк — делаем в 50 строк

---

## 3. Функциональные требования

### Публичная часть
- Красивое меню по категориям
- Фото, название, описание, цена
- Кнопки: «Позвонить» (tel:) и «Как пройти» (Яндекс/Гугл карты)
- Полностью адаптивно под телефон
- Быстрая загрузка (вес CSS < 50 КБ)

### Админка (/admin)
- Простейший логин/пароль
- CRUD для блюд и категорий
- Загрузка фото с авто-сжатием (Pillow)
- Список всех блюд с превью и кнопками Редактировать/Удалить

### Будущее (уже запланировано)
- Поле `is_bestseller` (иконка звёздочки в меню)
- Поле `is_seasonal` или `is_new` (новинки/сезонное)
- Возможность менять порядок категорий и блюд вручную
- Баннер «Блюдо дня» или «Новинка недели»

---

## 4. Модели данных (SQLAlchemy)

```sql
categories
├── id
├── name            -- "Завтраки", "Кофе", "Десерты" и т.д.
├── order_num       -- для сортировки (по умолчанию по id)

dishes
├── id
├── name
├── description
├── price
├── image_path      -- например: /uploads/dishes/123.jpg
├── category_id
├── is_bestseller   -- BOOLEAN DEFAULT FALSE
├── is_seasonal     -- BOOLEAN DEFAULT FALSE
├── created_at

admin_users
├── id
├── username
├── password_hash


Финальная структура проекта (обязательная с этого момента)

kakao/
├── app/
│   ├── __init__.py             # create_app(), регистрация blueprints
│   ├── models.py
│   ├── forms.py
│   ├── utils.py                # загрузка и сжатие фото
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py             # публичное меню
│   │   └── admin.py            # всё под /admin
│   ├── templates/
│   │   ├── base.html
│   │   ├── menu.html
│   │   ├── admin/
│   │   │   ├── login.html
│   │   │   └── dashboard.html
│   │   └── partials/           # карточка блюда, хедер, футер
│   └── static/
│       ├── css/
│       │   ├── menu.css
│       │   ├── admin.css
│       │   └── login.css
│       ├── js/
│       │   └── scripts.js
│       └── img/
│           └── logo.png
├── uploads/                        # ← ВНЕ static! в .gitignore!
│   └── dishes/                     # все фото блюд
├── instance/
│   └── cafe.db                     # SQLite база
├── migrations/
├── config.py
├── run.py                          # from app import create_app; app.run()
├── requirements.txt
├── .env
├── .gitignore
└── plan.md