# Foodgram — социальная сеть для обмена рецептами

[![Foodgram Workflow](https://github.com/DariaBarashkina/foodgram/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/DariaBarashkina/foodgram/actions/workflows/main.yml)


## 📋 О проекте

Foodgram — это веб-приложение, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок», который позволяет создавать список продуктов для приготовления выбранных блюд.

### Возможности
- Публикация рецептов с фотографиями, ингредиентами и тегами
- Фильтрация рецептов по тегам
- Добавление рецептов в избранное
- Подписка на авторов
- Формирование списка покупок с суммированием ингредиентов
- Скачивание списка покупок в текстовом формате
- Аутентификация и авторизация пользователей
- Управление аватаром пользователя

Проект состоит из бэкенда на Django REST Framework и фронтенда на React, упакованных в Docker-контейнеры и автоматически разворачиваемых через CI/CD.

### Бэкенд
- Python 3.12
- Django 5.1.1
- Django REST Framework 3.15.2
- Djoser (аутентификация)
- Gunicorn
- PostgreSQL
- python-dotenv

### Фронтенд
- React
- HTTP-сервер для раздачи статики

### Инфраструктура
- Docker
- Docker Compose
- Nginx (gateway)
- GitHub Actions (CI/CD)
- Яндекс.Облако (хостинг)

## 📁 Структура проекта
```
    foodgram/
    ├── backend/ # Бэкенд на Django
    │ ├── api/ # API приложение
    │ ├── recipes/ # Приложение рецептов
    │ ├── users/ # Приложение пользователей
    │ ├── backend/ # Основные настройки Django
    │ ├── manage.py # Управляющий скрипт Django
    │ ├── requirements.txt # Зависимости Python
    │ ├── Dockerfile # Dockerfile для бэкенда
    │ └── .env.example # Пример переменных окружения
    ├── frontend/ # Фронтенд на React
    │ ├── Dockerfile # Dockerfile для фронтенда
    │ └── nginx.conf # Конфигурация nginx для фронтенда
    ├── infra/ # Инфраструктура
    │ ├── docker-compose.production.yml # Docker Compose для продакшена
    │ ├── nginx.conf # Конфигурация reverse proxy
    │ └── .env.example # Пример переменных окружения для Docker
    ├── data/ # Данные для загрузки
    │ └── ingredients.csv # Список ингредиентов
    ├── docs/ # Документация
    ├── .github/
    │ └── workflows/ # GitHub Actions
    │ └── foodgram_workflow.yml # CI/CD workflow
    └── README.md # Этот файл
```


## 🚀 Как развернуть проект

### Локальный запуск

1. **Клонируйте репозиторий**
```bash
git clone git@github.com:DariaBarashkina/kittygram_final.git
cd kittygram_final
```

2. **Создать и активировать виртуальное окружение**
* Для Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

* Для Windows:
```bash
python -m venv venv
source venv/Scripts/activate
```

3. **Установить зависимости**
* Для Linux/macOS:
```bash
python3 -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

* Для Windows:
```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

4. **Создать файл .env (в корне проекта) с переменными окружения**
```bash
touch .env
```

* Добавьте в .env:
```.env
# Django настройки
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*доменное имя*

# PostgreSQL параметры (можно оставить для совместимости)
POSTGRES_DB=kittygram
POSTGRES_USER=kittygram_user
POSTGRES_PASSWORD=kittygram_password
DB_HOST=db
DB_PORT=5432
```

5. **Выполнить миграции**
* Для Linux/macOS:
```bash
cd backend
python3 manage.py migrate
```

* Для Windows:
```bash
cd backend
python manage.py migrate
```

6. **Запустить проект**
* Для Linux/macOS:
```bash
python3 manage.py runserver
```

* Для Windows:
```bash
python manage.py runserver
```

## 🔄 CI/CD с GitHub Actions
Проект использует GitHub Actions для автоматического тестирования, сборки и деплоя.

### Процесс CI/CD

**При пуше в любую ветку:**
- Запускается линтер flake8 для бэкенда
- Проверяется стиль кода по PEP8

**При пуше в ветку main:**
- Собираются и публикуются Docker-образы на Docker Hub
- Выполняется деплой на продакшен сервер
- Отправляется уведомление в Telegram


### Для работы CI/CD нужно добавить в Secrets GitHub:

**Для работы CI/CD добавьте следующие секреты в настройках репозитория (Settings → Secrets and variables → Actions):**
- DOCKER_USERNAME — логин на Docker Hub
- DOCKER_PASSWORD — пароль или токен
- SERVER_HOST — IP сервера
- SERVER_USER — пользователь (yc-user)
- SSH_KEY — приватный SSH-ключ
- TELEGRAM_TO — ID чата в Telegram
- ELEGRAM_TOKEN — токен бота

## 👨‍💻 Автор
Daria Barashkina
GitHub: @DariaBarashkina