import os
import sys
import django
import csv
from django.utils.dateparse import parse_datetime

# Project rootni sys.path ga qo'shamiz
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Django settingsni ko'rsatamiz
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # sizning settings.py joylashgan modul nomi

django.setup()

from django.contrib.auth import get_user_model
from apps.customer.models import Profile

User = get_user_model()

CSV_FILE = 'auth_user.csv'

with open(CSV_FILE, newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        username = row['username']

        if User.objects.filter(username=username).exists():
            print(f"{username} already exists")
            continue

        date_joined = parse_datetime(row['date_joined']) if row['date_joined'] else None

        # agar password bo'sh bo'lsa, default 1111 beramiz
        password = row['password'] if row['password'] else '1111'

        user = User.objects.create(
            username=username,
            password=password,
            is_superuser=row['is_superuser'] == 't',
            is_staff=row['is_staff'] == 't',
            is_active=row['is_active'] == 't',
            date_joined=date_joined
        )

        # Django uchun passwordni hashlaymiz
        user.password = password  # to'g'ridan-to'g'ri saqlaymiz
        user.save()

        Profile.objects.create(
            origin=user,
            full_name="",
            phone_number=username
        )

        print(f"{username} imported successfully")
