// Глобальные данные категорий (для menu.html)
const categories = ['porridge', 'additions', 'breakfast', 'sandwiches', 'salads', 'hot-offers', 'coffee', 'non-coffee', 'cold-coffee', 'cocktails'];
let currentCategoryIndex = -1; // -1 означает, что категория ещё не выбрана

function showPage(pageId) {
    const home = document.getElementById('home');
    const menu = document.getElementById('menu');
    const contacts = document.getElementById('contacts');

    if (home) home.style.display = 'none';
    if (menu) menu.classList.remove('active');
    if (contacts) contacts.classList.remove('active');

    if (pageId === 'home') {
        if (home) home.style.display = 'block';
    } else {
        const page = document.getElementById(pageId);
        if (page) page.classList.add('active');
    }
}

function showCategoryItems(categoryId) {
    categories.forEach(cat => {
        const element = document.getElementById('items-' + cat);
        if (element) {
            element.classList.remove('active');
        }
    });

    const targetElement = document.getElementById('items-' + categoryId);
    if (targetElement) {
        targetElement.classList.add('active');
    }

    currentCategoryIndex = categories.indexOf(categoryId);

    const buttons = document.querySelectorAll('.menu-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    const activeBtn = Array.from(buttons).find(b => b.getAttribute('onclick')?.includes("showCategoryItems('" + categoryId + "')"));
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
}

function showHome() {
    categories.forEach(cat => {
        const page = document.getElementById(cat);
        if (page) page.classList.remove('active');
    });
    const home = document.getElementById('home');
    if (home) home.style.display = 'block';
}

// Прокрутка меню колесом мыши
document.addEventListener('DOMContentLoaded', () => {
    const menuScroll = document.querySelector('.menu-scroll');
    if (menuScroll) {
        menuScroll.addEventListener('wheel', (e) => {
            e.preventDefault();
            menuScroll.scrollLeft += e.deltaY;
        });
    }
});

// Скрываем все категории при загрузке (ничего не открыто до клика)
document.addEventListener('DOMContentLoaded', () => {
    categories.forEach(cat => {
        const element = document.getElementById('items-' + cat);
        if (element) element.classList.remove('active');
    });
    currentCategoryIndex = -1;
});

// Свайп-навигация между категориями
document.addEventListener('DOMContentLoaded', () => {
    const area = document.querySelector('.items-container');
    if (!area) return;

    let startX = 0;
    let startY = 0;
    let isMoving = false;
    const threshold = 50; // минимальная дистанция по X для свайпа
    const restraintY = 80; // ограничение по Y, чтобы отличать вертикальную прокрутку

    area.addEventListener('touchstart', (e) => {
        if (e.touches.length !== 1) return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        isMoving = true;
    }, { passive: true });

    area.addEventListener('touchend', (e) => {
        if (!isMoving) return;
        isMoving = false;
        if (currentCategoryIndex < 0) return; // если ничего не выбрано — свайп игнорируем

        const touch = e.changedTouches && e.changedTouches[0];
        if (!touch) return;
        const dx = touch.clientX - startX;
        const dy = Math.abs(touch.clientY - startY);

        if (dy > restraintY) return; // вертикальный жест — не считаем как свайп

        if (Math.abs(dx) >= threshold) {
            if (dx < 0 && currentCategoryIndex < categories.length - 1) {
                showCategoryItems(categories[currentCategoryIndex + 1]);
            }
            if (dx > 0 && currentCategoryIndex > 0) {
                showCategoryItems(categories[currentCategoryIndex - 1]);
            }
        }
    }, { passive: true });
});

// Функции для работы с модальным окном продукта
function openProductModal(cardElement) {
    const modal = document.getElementById('product-modal');
    if (!modal) return;

    // Получаем данные из карточки
    const nameElement = cardElement.querySelector('.item-name');
    const priceElement = cardElement.querySelector('.item-price');
    const imageElement = cardElement.querySelector('.item-image');
    const descriptionElement = cardElement.querySelector('.item-description');

    const name = nameElement ? nameElement.textContent : 'Название продукта';
    let price = priceElement ? priceElement.textContent.trim() : '0 м';
    price = price.replace(/₼/g, 'м');
    const imageUrl = imageElement ? window.getComputedStyle(imageElement).backgroundImage.slice(5, -2) : '';
    const description = descriptionElement ? descriptionElement.textContent : 'Шаблонное описание продукта. Здесь будет размещена подробная информация о блюде или напитке.';

    // Заполняем модальное окно
    document.getElementById('product-title').textContent = name;
    document.getElementById('product-price').textContent = price;
    document.getElementById('product-description').textContent = description;

    // Устанавливаем изображение
    const largeImage = document.getElementById('product-large-image');
    if (largeImage && imageUrl) {
        largeImage.style.backgroundImage = `url('${imageUrl}')`;
    }

    // Показываем модальное окно
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeProductModal() {
    const modal = document.getElementById('product-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function addToCart() {
    // Шаблонная функция для добавления в корзину
    alert('Товар добавлен в корзину');
    // Здесь можно добавить реальную логику добавления в корзину
}

// Добавляем обработчики кликов на карточки продуктов
document.addEventListener('DOMContentLoaded', () => {
    const itemCards = document.querySelectorAll('.item-card');
    itemCards.forEach(card => {
        card.addEventListener('click', (e) => {
            e.preventDefault();
            openProductModal(card);
        });
    });

    // Закрытие модального окна по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeProductModal();
            closeSearch();
            closeAdminLogin();
        }
    });
});

// Функции для работы с поиском
let allMenuItems = [];

async function loadAllMenuItems() {
    try {
        const response = await fetch('/api/menu');
        allMenuItems = await response.json();
    } catch (error) {
        console.error('Ошибка загрузки меню для поиска:', error);
    }
}

function openSearch() {
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.value = '';
            document.getElementById('search-results').innerHTML = '';
        }
    }
}

function closeSearch() {
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function performSearch(query) {
    if (!query || query.trim().length === 0) {
        document.getElementById('search-results').innerHTML = '';
        return;
    }

    const searchTerm = query.toLowerCase().trim();
    const results = allMenuItems.filter(item => {
        const name = (item.name || '').toLowerCase();
        const description = (item.description || '').toLowerCase();
        return name.includes(searchTerm) || description.includes(searchTerm);
    });

    const resultsContainer = document.getElementById('search-results');
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">Ничего не найдено</div>';
        return;
    }

    resultsContainer.innerHTML = results.map(item => {
        const imageStyle = item.image_url ? `background-image: url('/${item.image_url}');` : '';
        return `
            <div class="search-result-item" onclick="openSearchResult('${item.id}')">
                <div class="search-result-image" style="${imageStyle}"></div>
                <div class="search-result-info">
                    <div class="search-result-name">${escapeHtml(item.name)}</div>
                    <div class="search-result-description">${escapeHtml(item.description || '')}</div>
                    <div class="search-result-price">${escapeHtml((item.price || '—').replace(/₼/g, 'м'))}</div>
                </div>
            </div>
        `;
    }).join('');
}

function openSearchResult(itemId) {
    const item = allMenuItems.find(i => i.id == itemId);
    if (!item) return;

    // Находим категорию и показываем её
    showCategoryItems(item.category);
    closeSearch();

    // Прокручиваем к элементу после небольшой задержки
    setTimeout(() => {
        const grid = document.getElementById(`grid-${item.category}`);
        if (grid) {
            const cards = grid.querySelectorAll('.item-card');
            cards.forEach(card => {
                const nameEl = card.querySelector('.item-name');
                if (nameEl && nameEl.textContent.trim() === item.name) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    // Подсвечиваем карточку
                    card.style.transition = 'all 0.3s';
                    card.style.transform = 'scale(1.05)';
                    card.style.boxShadow = '0 5px 20px rgba(0, 102, 204, 0.3)';
                    setTimeout(() => {
                        card.style.transform = '';
                        card.style.boxShadow = '';
                    }, 2000);
                }
            });
        }
    }, 300);
}

// Инициализация поиска
document.addEventListener('DOMContentLoaded', () => {
    loadAllMenuItems();
    
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(e.target.value);
            }, 300);
        });
    }
});

// Функции для работы с авторизацией админа
function openAdminLogin() {
    const modal = document.getElementById('admin-login-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.getElementById('admin-username').focus();
    }
}

function closeAdminLogin() {
    const modal = document.getElementById('admin-login-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        document.getElementById('admin-login-form').reset();
        document.getElementById('admin-login-error').style.display = 'none';
    }
}

async function handleAdminLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('admin-username').value;
    const password = document.getElementById('admin-password').value;
    const errorDiv = document.getElementById('admin-login-error');

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/admin/login', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Перенаправляем на админ-панель
            window.location.href = '/admin';
        } else {
            errorDiv.textContent = data.error || 'Неверный логин или пароль';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Ошибка соединения. Попробуйте еще раз.';
        errorDiv.style.display = 'block';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function handleLogoError() {
    const logoImage = document.getElementById('logo-image');
    const logoFallback = document.getElementById('logo-fallback');
    if (logoImage) logoImage.style.display = 'none';
    if (logoFallback) logoFallback.style.display = 'block';
}

