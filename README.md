# 🤖 OLX Bot — поиск выгодных сделок

## Структура проекта

```
olx_bot/
├── main.py                  # Точка входа
├── config/
│   └── settings.py          # Настройки через .env
├── bot/
│   ├── handlers/            # Обработчики команд
│   ├── keyboards/           # Клавиатуры
│   └── middlewares/         # DB middleware
├── parsers/
│   └── olx_parser.py        # GraphQL парсер OLX с антибаном
├── services/
│   ├── analytics.py         # Flip Score, ROI, проверка продавца
│   ├── monitor.py           # Фоновый мониторинг
│   └── export_service.py    # Экспорт CSV/Excel/JSON
├── database/
│   ├── models/              # SQLAlchemy модели
│   ├── repositories/        # Репозитории данных
│   └── engine.py            # Подключение к БД
└── utils/
    └── logger.py            # Логирование
```

## Быстрый старт

### 1. Настройка окружения

```bash
cp .env.example .env
# Заполните .env вашими значениями
```

`.env`:
```
BOT_TOKEN=ваш_токен
ADMIN_IDS=ваш_telegram_id
DATABASE_URL=postgresql+asyncpg://olxbot:olxpass@db:5432/olx_bot
REDIS_URL=redis://redis:6379/0
PARSE_INTERVAL_SECONDS=45
MIN_FLIP_SCORE=60
```

### 2. Запуск через Docker (рекомендуется)

```bash
docker-compose up -d --build
```

### 3. Запуск локально

```bash
pip install -r requirements.txt

# Поднимите PostgreSQL и Redis локально, затем:
python main.py
```

## Команды бота

| Команда | Описание |
|---------|----------|
| /start | Главное меню |
| /searches | Мои поисковые запросы |
| /add | Добавить поиск |
| /favorite | Избранные объявления |
| /stats | Статистика сделок |
| /settings | Фильтры и настройки |
| /export | Экспорт (CSV/Excel/JSON) |
| /admin | Панель администратора |

## Flip Score (0–100)

| Оценка | Значение |
|--------|----------|
| 95–100 🔥 | Отличная сделка |
| 80–95 ⭐️ | Хорошая сделка |
| 60–80 📊 | Средняя сделка |
| < 60 | Не отправляется |

Настроить порог: `MIN_FLIP_SCORE` в `.env`

## Антибан система

- Случайные задержки 1–4 сек между запросами
- Ротация User-Agent (5 браузеров)
- Поддержка прокси-листа (`PROXIES` в `.env`)
- Автоматический retry (3 попытки)
- При 429/403 — смена прокси + увеличенная пауза

## Добавление прокси

В `.env`:
```
PROXIES=http://user:pass@host1:port,http://user:pass@host2:port
```
