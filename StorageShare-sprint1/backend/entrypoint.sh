#!/bin/sh
set -eu
python manage.py migrate --noinput
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    python manage.py seed_storage_points
fi
exec python manage.py runserver 0.0.0.0:8000
