# StorageShare — Sprint 1

Единый проект из веток `birzhan`, `feat/IPM-9-auth-pages`, `docs/db-schema`, `dastan`.
Frontend: React + Vite. Backend: Django + DRF + JWT. БД для Docker: PostgreSQL 16.

## Быстрый запуск через Docker Desktop

Откройте терминал в этой папке (рядом с `docker-compose.yml`):

```sh
docker compose up --build -d
```

Первый запуск скачивает образы и зависимости. Backend автоматически применяет миграции
и загружает демонстрационные данные. Отдельно создавать `.env` для запуска не нужно.

- Приложение: http://localhost:8080
- Проверка backend и БД: http://localhost:8000/api/health/
- Логи: `docker compose logs -f`
- Остановка без удаления данных: `docker compose down`

Войдите как партнёр: `hostel@example.com`, пароль `SeedPartner2026`.
Или зарегистрируйте нового путешественника через форму. Всего создано 6 точек в районах
Медеу, Алмалы и Бостандык. В остальных районах список пуст — это нормальный сценарий.
Повторный seed обновляет демо-точки. Чтобы отключить его, задайте `SEED_DEMO_DATA=0`
в корневом `.env` (образец: `.env.example`).

Это конфигурация локальной разработки и демонстрации: Django runserver, открытые
демо-пароли и локальный SECRET_KEY. Публикация в интернете требует отдельной настройки.
Для удаления всех локальных данных: `docker compose down -v` (удаляет БД).
Если 8080 или 8000 занят, поменяйте левый порт в Compose.

## Запуск без Docker

Нужны Python 3.12+ и Node.js 24. Для разработки можно использовать SQLite;
PostgreSQL используется в Compose. Команды ниже выполняются из корня проекта.

Windows PowerShell, первый терминал:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
$env:DATABASE_URL = 'sqlite:///db.sqlite3'
$env:DEBUG = '1'
cd backend
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py seed_storage_points
..\.venv\Scripts\python.exe manage.py runserver
```

Второй терминал:

```sh
cd frontend
npm ci
npm run dev
```

Откройте http://localhost:5173. Vite перенаправляет `/api` на `127.0.0.1:8000`.
При подключении к другому backend задайте `VITE_API_BASE_URL` в `frontend/.env`
и настройте CORS на сервере. Шаблон: `frontend/.env.example`.
Не копируйте `backend/.env.example` для варианта SQLite: он содержит адрес БД Docker.

Linux/macOS, backend:

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend
export DATABASE_URL=sqlite:///db.sqlite3
export DEBUG=1
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_storage_points
../.venv/bin/python manage.py runserver
```

## Проверки

При запущенном Compose:

```sh
docker compose exec backend python manage.py test
docker compose exec backend python manage.py makemigrations --check --dry-run
```

Frontend (локально, нужны Node.js и `npm ci`):

```sh
cd frontend
npm run lint
npm run build
```

API smoke-тест (требует запущенное приложение и демо-данные):

```sh
python scripts/api_smoke.py http://localhost:8080
```

Результаты проверки готового архива: [docs/verification.md](docs/verification.md).

## Что входит в Sprint 1

- Регистрация с обязательными именем, email, паролем и явным выбором роли.
- Настоящий вход, JWT access/refresh, восстановление сессии через `/auth/me/`.
- Автоматическое обновление токенов, выход с отзывом refresh, защита страниц.
- Карточки точек, фильтр по 8 районам, пустое состояние и обработка ошибок.
- Детали точки: адрес, район, цена за сумку в час, часы, сведения о безопасности.
- Русский, казахский и английский интерфейс; адреса и названия точек приходят из БД.
- Кабинет партнёра — явно обозначенная заглушка. CRUD точек, бронирования и QR
  относятся к следующим этапам и здесь не реализованы.

Токены сохраняются в localStorage для этого MVP; не добавляйте непроверенные скрипты.
Выход отзывает refresh; уже выданный access сохраняет срок действия (до 30 минут).

## Как перенести в существующий Git-репозиторий

Из корня своего репозитория:

```sh
git switch main
git pull --ff-only
git switch -c integration/sprint-1
```

Скопируйте **содержимое** папки `StorageShare` из архива в корень репозитория,
с заменой совпадающих файлов. Саму папку `.git` не трогайте. Если уже есть локальные
`.env`, обновите их вручную по образцам, не коммитьте их. Затем проверьте:

```sh
git status
git diff --stat
```

Запустите проект и проверки выше. После проверки:

```sh
git add .
git commit -m "Integrate Sprint 1 frontend and backend"
git push -u origin integration/sprint-1
```

Затем создайте Pull Request в `main`. ZIP содержит итоговые файлы, но не Git-историю
исходных веток; коммиты ребят сохраняются в их ветках.

## Документация

- `docs/api-auth.md` — актуальный контракт авторизации.
- `docs/api-storage-points.md` — актуальный контракт точек и районов.
- `docs/frontend-integration-notes.md` — что изменено при интеграции.
- `docs/db-schema.md` — актуальная схема реализованных таблиц.
- `docs/db-schema-original.md` и `.png` — исходный проект схемы, исторический материал.
- `docs/wireframes/` — исходные вайрфреймы Биржана; их HTTP 409 заменён на реальный 400.
