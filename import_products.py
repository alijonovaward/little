import os
import sys
import django
import csv
from datetime import datetime

# Django project root path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # settings.py joyi
django.setup()

from apps.product.models import ProductItem, Good, Category

# --- Helper function ---
def parse_datetime(value):
    if not value:
        return None
    # +00 ni +00:00 ga o'zgartirish
    if value.endswith("+00"):
        value = value + ":00"
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f%z")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")

# --- Import ProductItem ---
PRODUCTITEM_CSV = "product_productitem.csv"
with open(PRODUCTITEM_CSV, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Agar id bilan saqlash kerak bo'lsa:
        product_id = int(row["id"])
        
        # Avval mavjud bo'lsa update, bo'lmasa create
        product, created = ProductItem.objects.update_or_create(
            id=product_id,
            defaults={
                "desc": row.get("desc") or "",
                "measure": int(row.get("measure") or 0),
                "available_quantity": int(row.get("available_quantity") or 0),
                "bonus": int(row.get("bonus") or 0),
                "active": row.get("active", "t") == "t",
                "new_price": int(row.get("new_price") or 0),
                "old_price": int(row.get("old_price") or 0),
                "weight": float(row.get("weight") or 1),
                "product_type": row.get("product_type") or None,
                "main": row.get("main", "t") == "t",
            },
        )
        print(f"ProductItem {product.id} - {'Created' if created else 'Updated'}")

# --- Import Good ---
GOOD_CSV = "product_good.csv"
with open(GOOD_CSV, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        good_id = int(row["id"])
        # category uchun id olamiz
        cat_id = row.get("sub_cat_id")
        category = Category.objects.filter(id=cat_id).first() if cat_id else None

        # product uchun id olamiz
        prod_id = row.get("product_id")
        product = ProductItem.objects.filter(id=prod_id).first() if prod_id else None

        good, created = Good.objects.update_or_create(
            id=good_id,
            defaults={
                "name": row.get("name") or "",
                "ingredients": row.get("ingredients") or "",
                "expire_date": row.get("expire_date") or None,
                "category": category,
                "product": product,
            },
        )
        print(f"Good {good.id} - {'Created' if created else 'Updated'}")
