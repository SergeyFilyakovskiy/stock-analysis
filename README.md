# Stock Analysis Platform

Микросервисная платформа для анализа фондового рынка. Предоставляет котировки в реальном времени, исторические OHLCV-данные, фундаментальный и технический анализ, управление портфелем и уведомления через WebSocket.

## Архитектура

```
                          ┌─────────────────────────────────┐
                          │         Traefik v3 (gateway)     │
                          │  api.localhost · app.localhost   │
                          └────────────┬────────────────────┘
                                       │  JWT forwardAuth → auth-service
                   ┌───────────────────┼──────────────────────────┐
                   │                   │                           │
          ┌────────▼──────┐  ┌─────────▼──────┐  ┌───────────────▼──────┐
          │  auth-service │  │ market-service  │  │ fundamental-service  │
          │  /api/v1/auth │  │ /api/v1/market  │  │ /api/v1/fundamental  │
          └───────────────┘  └────────┬────────┘  └──────────────────────┘
                                      │ gRPC :50051
          ┌───────────────┐  ┌────────▼────────┐  ┌──────────────────────┐
          │  portfolio-   │  │ technical-      │  │ notification-service  │
          │  service      │  │ service         │  │ /ws  (WebSocket)      │
          │  /api/v1/port │  │ /api/v1/tech    │  └──────────────────────┘
          └───────────────┘  └─────────────────┘
                   │
    ┌──────────────┼─────────────────────┐
    │              │                     │
 TimescaleDB    Redis 7             RabbitMQ 3.13
 (pg16)         (pub/sub · cache)   (events)
```

### Сервисы

| Сервис | Порт (внутренний) | Описание |
|---|---|---|
| `auth-service` | 8000 | Регистрация, JWT-аутентификация, OAuth (Google, GitHub) |
| `market-service` | 8000 / 50051 | Котировки, OHLCV, дивиденды, индексы; gRPC-сервер |
| `fundamental-service` | 8000 | Финансовые отчёты, оценка (DCF, EV/EBITDA, P/E), скринер |
| `technical-service` | 8000 | Индикаторы (SMA, EMA, RSI, MACD, Bollinger), паттерны |
| `portfolio-service` | 8000 | Портфели, транзакции, вотчлисты, ценовые алерты |
| `notification-service` | 8000 | WebSocket-броадкаст обновлений цен и событий |

### Инфраструктура

| Компонент | Назначение |
|---|---|
| Traefik v3 | API Gateway, TLS, rate-limit, CORS, JWT forwardAuth |
| TimescaleDB (pg16) | Хранение OHLCV, финансовых отчётов, портфелей |
| Redis 7 | Кэш цен, JWT-блэклист, pub/sub для WebSocket |
| RabbitMQ 3.13 | Асинхронные события между сервисами |
| Celery + Beat | Периодическая загрузка рыночных данных |
| Prometheus + Grafana | Мониторинг и дашборды |

---

## Быстрый старт

### Требования

- Docker ≥ 25 и Docker Compose v2
- TLS-сертификаты для Traefik (самоподписанные для dev)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/SergeyFilyakovskiy/stock-analysis.git
cd stock-analysis
```

### 2. Настроить переменные окружения

```bash
cp .env.example .env
```

Заполнить `.env` (обязательные поля описаны в разделе [Переменные окружения](#переменные-окружения)).

### 3. Сгенерировать TLS-сертификаты

```bash
mkdir -p traefik/certs
openssl req -x509 -newkey rsa:4096 -keyout traefik/certs/key.pem \
  -out traefik/certs/cert.pem -days 365 -nodes \
  -subj "/CN=localhost"
```

### 4. Настроить basic-auth для Prometheus

```bash
# Установить htpasswd (apache2-utils / httpd-tools)
htpasswd -nB admin
# Вставить полученную строку в traefik/dynamic/middlewares.yml → basic-auth.users
```

### 5. Добавить локальные хосты

```bash
# /etc/hosts
127.0.0.1  api.localhost app.localhost grafana.localhost prometheus.localhost rabbitmq.localhost
```

### 6. Запустить

```bash
docker compose up -d
```

Миграции БД запускаются автоматически через `market-migrate` (и аналогичные контейнеры, если добавить для других сервисов).

---

## Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `POSTGRES_USER` | Пользователь PostgreSQL | `postgres` |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | — |
| `REDIS_PASSWORD` | Пароль Redis | — |
| `RABBITMQ_PASSWORD` | Пароль RabbitMQ | — |
| `JWT_SECRET` | Секрет для подписи JWT | случайная строка ≥ 32 символа |
| `JWT_ALGORITHM` | Алгоритм JWT | `HS256` |
| `JWT_ACCESS_EXPIRE` | TTL access-токена (секунды) | `900` |
| `JWT_REFRESH_EXPIRE` | TTL refresh-токена (секунды) | `2592000` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | — |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | — |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | — |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret | — |
| `ALPHA_VANTAGE_API_KEY` | Ключ Alpha Vantage | — |
| `POLYGON_API_KEY` | Ключ Polygon.io | — |
| `GRAFANA_ADMIN_PASSWORD` | Пароль admin в Grafana | — |
| `PRICE_FETCH_INTERVAL_SECONDS` | Интервал опроса цен Celery | `60` |
| `MARKET_GRPC_HOST` | Хост gRPC market-service | `market-service` |
| `MARKET_GRPC_PORT` | Порт gRPC market-service | `50051` |

---

## API

Все запросы идут через `https://api.localhost`. Защищённые эндпоинты требуют заголовка:

```
Authorization: Bearer <access_token>
```

### Auth — `/api/v1/auth`

| Метод | Путь | Описание | Авторизация |
|---|---|---|---|
| `POST` | `/register` | Регистрация | — |
| `POST` | `/login` | Вход, возвращает access + refresh токены | — |
| `POST` | `/logout` | Выход (инвалидирует токены) | ✓ |
| `POST` | `/refresh` | Обновление access-токена | — |
| `GET` | `/profile` | Профиль текущего пользователя | ✓ |
| `GET` | `/verify` | Верификация токена (используется Traefik forwardAuth) | ✓ |
| `GET` | `/oauth/google` | Редирект на Google OAuth | — |
| `GET` | `/oauth/google/callback` | Callback Google OAuth | — |
| `GET` | `/oauth/github` | Редирект на GitHub OAuth | — |
| `GET` | `/oauth/github/callback` | Callback GitHub OAuth | — |

### Market — `/api/v1/market`

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/securities` | Список бумаг (поиск по тикеру и названию) |
| `GET` | `/securities/{ticker}` | Детали бумаги |
| `GET` | `/securities/{ticker}/history` | OHLCV история (`interval`: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`) |
| `GET` | `/securities/{ticker}/last-price` | Последняя цена |
| `GET` | `/dividends/{ticker}` | Дивиденды |
| `GET` | `/indices` | Индексы |
| `GET` | `/overview` | Обзор рынка |
| `WS` | `wss://api.localhost/ws/stream/{ticker}?token=<jwt>` | Стрим цены в реальном времени |

### Fundamental — `/api/v1/fundamental`

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/companies/{ticker}` | Метрики компании |
| `GET` | `/companies/{ticker}/reports` | Финансовые отчёты |
| `GET` | `/screener` | Скринер по фундаментальным показателям |
| `GET` | `/compare` | Сравнение нескольких компаний |

### Technical — `/api/v1/technical`

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/indicators/{ticker}` | Технические индикаторы (SMA, EMA, RSI, MACD, Bollinger) |
| `GET` | `/patterns/{ticker}` | Свечные паттерны |
| `GET` | `/signals/{ticker}` | Торговые сигналы |

### Portfolio — `/api/v1/portfolio`

| Метод | Путь | Описание |
|---|---|---|
| `GET/POST` | `/portfolios` | Список / создание портфеля |
| `GET/DELETE` | `/portfolios/{id}` | Детали / удаление |
| `GET/POST` | `/portfolios/{id}/transactions` | Транзакции |
| `GET` | `/portfolios/{id}/analytics` | Аналитика (P&L, состав) |
| `GET/POST/DELETE` | `/watchlists` | Вотчлисты |
| `GET/POST/DELETE` | `/alerts` | Ценовые алерты |

---

## OAuth — настройка

### Google

1. [Google Cloud Console](https://console.cloud.google.com) → Credentials → OAuth 2.0 Client IDs
2. Authorized redirect URIs:
   ```
   https://api.localhost/api/v1/auth/oauth/google/callback
   ```
3. Вставить `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET` в `.env`

### GitHub

1. GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
2. Authorization callback URL:
   ```
   https://api.localhost/api/v1/auth/oauth/github/callback
   ```
3. Вставить `GITHUB_CLIENT_ID` и `GITHUB_CLIENT_SECRET` в `.env`

---

## Мониторинг

| Интерфейс | URL |
|---|---|
| Traefik Dashboard | http://localhost:8080 |
| Prometheus | http://prometheus.localhost (basic-auth) |
| Grafana | http://grafana.localhost (admin / `GRAFANA_ADMIN_PASSWORD`) |
| RabbitMQ Management | http://rabbitmq.localhost |

---

## Структура репозитория

```
stock-analysis/
├── services/
│   ├── auth-service/        # Аутентификация и авторизация
│   ├── market-service/      # Рыночные данные + Celery workers
│   ├── fundamental-service/ # Фундаментальный анализ
│   ├── technical-service/   # Технический анализ
│   ├── portfolio-service/   # Портфели и алерты
│   └── notification-service/# WebSocket уведомления
├── frontend/                # React + TypeScript SPA
├── traefik/
│   ├── traefik.yml          # Основная конфигурация Traefik
│   ├── dynamic/
│   │   ├── middlewares.yml  # Rate-limit, CORS, JWT, basic-auth
│   │   └── tsl.yml          # TLS-сертификаты
│   └── certs/               # cert.pem + key.pem (gitignored)
├── db/
│   └── init/                # SQL-скрипт создания баз данных
├── prometheus/
│   └── prometheus.yml       # Конфигурация сбора метрик
├── grafana/
│   └── provisioning/        # Дашборды и источники данных
├── docker-compose.yml
└── .env.example
```

---

## Разработка

### Запуск отдельного сервиса локально

```bash
cd services/auth-service
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Миграции

```bash
cd services/market-service
uv run alembic upgrade head
```

### Celery worker (market-service)

```bash
uv run celery -A app.workers.celery_app worker --loglevel=info
uv run celery -A app.workers.celery_app beat --loglevel=info
```

---

## Технологический стек

**Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, python-jose, authlib, Celery, gRPC  
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, lightweight-charts  
**Инфраструктура:** Docker Compose, Traefik v3, TimescaleDB (pg16), Redis 7, RabbitMQ 3.13  
**Мониторинг:** Prometheus, Grafana, postgres-exporter, redis-exporter
