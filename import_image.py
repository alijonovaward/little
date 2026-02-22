import os
import sys
import django
import csv

# Django settings ga yo'l
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.product.models import ProductItem, Image

IMAGE_CSV = "product_image.csv"

with open(IMAGE_CSV, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        try:
            product_id = int(row["product_id"])
            product = ProductItem.objects.filter(id=product_id).first()
            if not product:
                print(f"ProductItem id={product_id} topilmadi, o'tkazildi.")
                continue

            image_path = row["image"].replace("images/", "")

            obj, created = Image.objects.update_or_create(
                product=product,
                image=f"images/{image_path}",  # ImageField uchun path
                defaults={
                    "name": row.get("name_uz") or row.get("name")  # English nomi bo'lmasa original name
                },
            )

            action = "Created" if created else "Updated"
            print(f"{action} Image '{obj.name}' for ProductItem {product.id}")

        except Exception as e:
            print(f"Xatolik: {e} | Row: {row}")
