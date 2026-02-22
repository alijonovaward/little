#!/usr/bin/env bash
# exit on error
set -o errexit

# Pip-ni yangilaymiz va setuptools-ni o'rnatamiz (drf-yasg uchun pkg_resources kerak)
python -m pip install --upgrade pip
pip install setuptools

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# MANA SHU QATORLARNI QO'SHING:
mkdir -p /opt/render/project/src/mediafiles
chmod -R 777 /opt/render/project/src/mediafiles
