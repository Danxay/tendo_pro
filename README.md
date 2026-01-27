# Telegram Bot (aiogram)

## Быстрый старт

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Задайте переменные окружения:

- `BOT_TOKEN` — токен Telegram-бота
- `ADMIN_CODE` — код администратора (по умолчанию `0000`)
- `ADMIN_PHONES` — список телефонов администраторов через запятую
- `DB_PATH` — путь к SQLite базе (по умолчанию `data/bot.db`)

Пример:

```bash
export BOT_TOKEN="123:abc"
export ADMIN_CODE="4321"
export ADMIN_PHONES="+79991234567,+79990001122"
```

3. Запуск:

```bash
python3 -m app.main
```

## Тесты

```bash
python3 -m unittest discover -s tests
```

## Админ-команды

- `/admin_add +79991234567` — добавить администратора
- `/admin_remove +79991234567` — удалить администратора
- `/block +79991234567` — заблокировать пользователя
- `/unblock +79991234567` — разблокировать пользователя
- `/reviews` — выгрузить отзывы
