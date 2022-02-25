# Yatube

Соц.сеть для ведения личных дневников. В соц.сети можно публиковать свои записи, читать и подписываться на других авторов. Ставить лайки и дизлайки.

Данный проект был реализован по MVT архитектуре для изучения функционала фреймворка, а именно:
- Настройка пагинации постов и кеширование 
- Настройка регистрации с верификацией данных и сменой паролей через почтовый сервер
- Написание собственных юнит-тестов

## Технологии
- Python 3.7
- Django 3.0.5

## Установка

1. Клонируйте репозиторий на локальный компьютер
2. Создайте и активируйте виртуальное окружение
```bash
python3 -m venv venv
. venv/bin/activate
```
3. Установите зависимости
```bash
pip install -r requirements.txt
```
4. Выполните миграции
```bash
python manage.py makemigrations users
python manage.py makemigrations
python manage.py migrate
```
5. Создайте администратора
```bash
python manage.py createsuperuser
```
6. Запустите проект локально
```bash
python manage.py runserver
```
Готово, проект доступен по адресу http://127.0.0.1:8000/

## Автор

- Хюппенен Артём
