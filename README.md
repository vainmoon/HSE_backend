# HSE_backend
This repository contains homework assignments on the subject "backend development" in Python as part of the HSE Master's program in Machine Learning in Digital Products.

# Запуск

## Сервис

```bash
cd docker
docker compose up -d
```

API доступен на http://localhost:8000

## Воркер Kafka

Запускается автоматически вместе с `docker compose up -d`. Для просмотра логов:

```bash
docker compose logs -f worker
```

## Тесты

Все тесты:
```bash
docker compose --profile test run --rm tests
```

Только юнит-тесты:
```bash
docker compose --profile test run --rm tests pytest -v -m "not integration"
```

Только интеграционные тесты:
```bash
docker compose --profile test run --rm tests pytest -v -m integration
```
