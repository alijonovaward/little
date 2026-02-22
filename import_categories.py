import os
import sys
import django
import csv
from django.utils.dateparse import parse_datetime

# Project rootni sys.path ga qo‘shamiz
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# SETTINGS (KECHAGI KABI)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from apps.product.models import Category

CSV_FILE = 'product_category.csv'


with open(CSV_FILE, newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)

    for row in reader:
        category_id = int(row['id'])

        category, created = Category.objects.update_or_create(
            id=category_id,
            defaults={
                "main_type": row["main_type"],
                "name": row["name"],
                "image": row["image"],
                "desc": row["desc"] or "",
                "active": row["active"].lower() == "t",
            }
        )

        # created / modified ni to‘g‘ri parse qiladi (Django built-in)
        if row.get("created"):
            category.created = parse_datetime(row["created"])

        if row.get("modified"):
            category.modified = parse_datetime(row["modified"])

        category.save()

        print(f"✔ Imported: {category.id} - {category.name}")

print("✅ DONE")
