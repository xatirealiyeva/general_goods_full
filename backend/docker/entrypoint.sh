#!/bin/sh
set -e

echo "Waiting for database..."
python - << 'PYEOF'
import os, time, sys
import psycopg2

host = os.environ.get("POSTGRES_HOST")
if host:
    for _ in range(30):
        try:
            psycopg2.connect(
                dbname=os.environ.get("POSTGRES_DB", "shopdb"),
                user=os.environ.get("POSTGRES_USER", "shopuser"),
                password=os.environ.get("POSTGRES_PASSWORD", "shoppass"),
                host=host,
                port=os.environ.get("POSTGRES_PORT", "5432"),
            ).close()
            print("Database is up.")
            sys.exit(0)
        except Exception as e:
            print("Database not ready, retrying...", e)
            time.sleep(1)
    print("Database never became ready.")
    sys.exit(1)
else:
    print("No POSTGRES_HOST set, skipping wait (using SQLite).")
PYEOF

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "${RUN_SEED_DEMO_DATA:-false}" = "true" ]; then
    echo "Seeding demo data..."
    python manage.py seed_demo_data
fi

echo "Starting server..."
if [ "$1" = "gunicorn" ]; then
    exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-3}"
fi
exec "$@"
