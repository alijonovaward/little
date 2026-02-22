import os
import json
import django
import uuid

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

from apps.product.models import Category, ProductItem, Good, Phone, Ticket, Image
from django.db import transaction

def restore_data(json_file):
    with open(json_file, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    print(f"Starting restoration from {json_file}...")

    # Organize data by model
    categories = [item for item in data if item['model'] == 'product.category']
    product_items = [item for item in data if item['model'] == 'product.productitem']
    goods = [item for item in data if item['model'] == 'product.good']
    phones = [item for item in data if item['model'] == 'product.phone']
    tickets = [item for item in data if item['model'] == 'product.ticket']
    images = [item for item in data if item['model'] == 'product.image']

    with transaction.atomic():
        # 1. Restore Categories
        print("Restoring Categories...")
        cat_map = {} # old_pk -> new_obj
        for item in categories:
            fields = item['fields']
            # Clean translation fields if they are null but required or problematic
            obj, created = Category.objects.update_or_create(
                id=item['pk'],
                defaults={
                    "main_type": fields.get('main_type', 'f'),
                    "name": fields.get('name', ''),
                    "name_uz": fields.get('name_uz'),
                    "name_ru": fields.get('name_ru'),
                    "name_en": fields.get('name_en'),
                    "name_ko": fields.get('name_ko'),
                    "desc": fields.get('desc', ''),
                    "desc_uz": fields.get('desc_uz'),
                    "desc_ru": fields.get('desc_ru'),
                    "desc_en": fields.get('desc_en'),
                    "desc_ko": fields.get('desc_ko'),
                    "active": fields.get('active', True),
                }
            )
            cat_map[item['pk']] = obj
            print(f"  Category: {obj.name} ({'Created' if created else 'Updated'})")

        # 2. Restore ProductItems
        print("Restoring ProductItems...")
        pi_map = {}
        for item in product_items:
            fields = item['fields']
            # product_type might be a string or UUID in JSON
            ptype = fields.get('product_type')
            if isinstance(ptype, str):
                try:
                    ptype = uuid.UUID(ptype)
                except ValueError:
                    ptype = uuid.uuid4()

            obj, created = ProductItem.objects.update_or_create(
                id=item['pk'],
                defaults={
                    "desc": fields.get('desc', ''),
                    "product_type": ptype,
                    "old_price": fields.get('old_price', 0),
                    "new_price": fields.get('new_price', 0),
                    "b2b_price": fields.get('b2b_price', 0),
                    "min_wholesale_quantity": fields.get('min_wholesale_quantity', 1),
                    "weight": fields.get('weight', 1.0),
                    "measure": fields.get('measure', 0),
                    "available_quantity": fields.get('available_quantity', 0),
                    "bonus": fields.get('bonus', 0),
                    "discount_price": fields.get('discount_price', 0),
                    "main": fields.get('main', True),
                    "active": fields.get('active', True),
                }
            )
            pi_map[item['pk']] = obj

        # 3. Restore Goods
        print("Restoring Goods...")
        for item in goods:
            fields = item['fields']
            product = pi_map.get(fields.get('product'))
            category = cat_map.get(fields.get('category'))
            if not product: continue
            
            Good.objects.update_or_create(
                id=item['pk'],
                defaults={
                    "name": fields.get('name', ''),
                    "product": product,
                    "ingredients": fields.get('ingredients'),
                    "expire_date": fields.get('expire_date'),
                    "category": category,
                }
            )

        # 4. Restore Phones
        print("Restoring Phones...")
        for item in phones:
            fields = item['fields']
            product = pi_map.get(fields.get('product'))
            category = cat_map.get(fields.get('category'))
            if not product: continue
            
            Phone.objects.update_or_create(
                id=item['pk'],
                defaults={
                    "model_name": fields.get('model_name', ''),
                    "product": product,
                    "color": fields.get('color', 'black'),
                    "condition": fields.get('condition', 'new'),
                    "ram": fields.get('ram', '0'),
                    "storage": fields.get('storage', '0'),
                    "category": category,
                }
            )

        # 5. Restore Tickets
        print("Restoring Tickets...")
        for item in tickets:
            fields = item['fields']
            product = pi_map.get(fields.get('product'))
            category = cat_map.get(fields.get('category'))
            if not product: continue
            
            Ticket.objects.update_or_create(
                id=item['pk'],
                defaults={
                    "event_name": fields.get('event_name', ''),
                    "product": product,
                    "category": category,
                }
            )

        # 6. Restore Images
        print("Restoring Images...")
        for item in images:
            fields = item['fields']
            product = pi_map.get(fields.get('product'))
            if not product: continue
            
            Image.objects.update_or_create(
                id=item['pk'],
                defaults={
                    "image": fields.get('image'),
                    "name": fields.get('name'),
                    "product": product,
                }
            )

    print("Restoration complete!")

if __name__ == "__main__":
    restore_data('product.json')
