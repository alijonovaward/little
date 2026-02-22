import os
import sys
import django
import csv
from datetime import datetime

# Django project root path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.product.models import ProductItem, SoldProduct
from apps.customer.models import Profile  # user model

CSV_FILE = "product_soldproduct.csv"

with open(CSV_FILE, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        try:
            product_id = row.get("product_id")
            user_id = row.get("user_id")
            
            product = ProductItem.objects.filter(id=product_id).first() if product_id else None
            user = Profile.objects.filter(id=user_id).first() if user_id else None

            amount = row.get("amount") or 0
            quantity = row.get("quantity") or 0

            obj, created = SoldProduct.objects.update_or_create(
                id=row["id"],  # agar id bo'yicha unique saqlamoqchi bo'lsak
                defaults={
                    "product": product,
                    "user": user,
                    "amount": amount,
                    "quantity": quantity,
                },
            )

            action = "Created" if created else "Updated"
            print(f"{action} SoldProduct id={obj.id}")

        except Exception as e:
            print(f"Xatolik: {e} | Row: {row}")
