#!/bin/sh
set -e

python manage.py migrate --fake
python manage.py collectstatic --noinput
python create_admin.py
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT


