# order-creation
Тестовое задание для JetLend

## Stack

- Django 6.0.3
- Django REST Framework
- PostgreSQL 15
- Docker Compose


## Запуск проекта

```bash
# скопировать (заполнить) .env
cp .env.example .env

# запуск контейнеров
docker compose up --build

# Сделать заказ
POST на /orders/
```
