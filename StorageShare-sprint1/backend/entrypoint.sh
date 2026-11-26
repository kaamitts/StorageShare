#!/bin/sh
set -eu
python manage.py migrate --noinput
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    python manage.py seed_storage_points
fi

# DEBUG=1 is local Docker Compose (code mounted, autoreload).
# Anything else (Render, etc.) runs gunicorn on the port the host provides.
if [ "${DEBUG:-0}" = "1" ]; then
    exec python manage.py runserver 0.0.0.0:8000
fi
python manage.py collectstatic --noinput
exec gunicorn config.wsgi --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 60
