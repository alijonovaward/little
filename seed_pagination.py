import os
import django
from datetime import date, timedelta

from decouple import config


def _setup_django() -> None:
    database_url = config("DATABASE_URL", default=None)
    if not database_url:
        raise SystemExit(
            "DATABASE_URL is required. Set it in your environment (or a local .env file) before running this script."
        )

    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


_setup_django()

from apps.product.models import Category, ProductItem, Good, Image
from django.db import transaction

def seed_pagination_test():
    print("Clearing database for pagination test...")
    with transaction.atomic():
        Good.objects.all().delete()
        Image.objects.all().delete()
        Category.objects.all().delete()
        ProductItem.objects.all().delete()
        print("Database cleared.")

        # 1. 5 Categories
        print("Creating 5 Categories...")
        cat_names = [
            {"uz": "Meva", "ru": "Фрукты", "en": "Fruits", "ko": "과일"},
            {"uz": "Sabzavot", "ru": "Овощи", "en": "Vegetables", "ko": "야채"},
            {"uz": "Sutli", "ru": "Молочные", "en": "Dairy", "ko": "유제품"},
            {"uz": "Ichimlik", "ru": "Напитки", "en": "Drinks", "ko": "음료"},
            {"uz": "Shirinlik", "ru": "Сладости", "en": "Sweets", "ko": "사탕"},
        ]
        
        cats = []
        for cn in cat_names:
            c = Category.objects.create(
                name_uz=cn['uz'], name_ru=cn['ru'], name_en=cn['en'], name_ko=cn['ko'],
                main_type="f"
            )
            cats.append(c)

        # 2. 5 Items per category (Total 25)
        print("Adding 5 items per category (Total 25)...")
        for i, cat in enumerate(cats):
            for j in range(1, 6):
                name_uz = f"{cat.name_uz} {j}"
                name_ru = f"{cat.name_ru} {j}"
                name_en = f"{cat.name_en} {j}"
                name_ko = f"{cat.name_ko} {j}"
                
                price = 1000 * (i + 1) + (j * 100)
                
                pi = ProductItem.objects.create(
                    desc_uz=f"{name_uz} tavsifi. Sifatli mahsulot.",
                    desc_ru=f"Описание {name_ru}. Качественный продукт.",
                    desc_en=f"Description of {name_en}. Quality product.",
                    desc_ko=f"{name_ko} 설명. 우수한 제품.",
                    new_price=price,
                    old_price=price + 500,
                    available_quantity=100,
                    main=True,
                    active=True
                )
                Good.objects.create(
                    product=pi, category=cat,
                    name_uz=name_uz, name_ru=name_ru, name_en=name_en, name_ko=name_ko,
                    expire_date=date.today() + timedelta(days=30)
                )

    print("Success! 25 items (5x5) added. Pagination (page_size=20) should now work.")

if __name__ == "__main__":
    seed_pagination_test()
