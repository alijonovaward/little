from django.core.management.base import BaseCommand
from apps.product.models import ProductItem, Category, Good
from apps.product import models as product_models
import uuid
import random

class Command(BaseCommand):
    help = 'Creates test data with products and variants for frontend testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test data...')
        
        # 1. Get or Create Category
        category, created = Category.objects.get_or_create(
            name='Oziq-ovqat Test',
            defaults={
                'name_uz': 'Oziq-ovqat Test',
                'name_ru': 'Test Food',
                'name_en': 'Test Food',
                'name_kr': 'Test Food',
                'main_type': 'f',
                'desc': 'Test category for food',
                'desc_uz': 'Test oziq-ovqat',
                'desc_ru': 'Test food desc',
                'desc_en': 'Test food desc',
                'desc_kr': 'Test food desc',
                'active': True
            }
        )
        if created:
            self.stdout.write(f'Created Category: {category.name}')
        else:
            self.stdout.write(f'Using existing Category: {category.name}')

        # Create a group of variants
        product_type_uuid = uuid.uuid4()
        
        variants_data = [
            {
                'name': 'Test Guruch 1kg',
                'weight': 1.0,
                'measure': 0, # KG
                'old_price': 25000,
                'new_price': 22000,
                'b2b_price': 20000,
                'wholesale_price': 19000,
                'min_wholesale_quantity': 10,
                'available_quantity': 100,
                'main': True 
            },
            {
                'name': 'Test Guruch 5kg',
                'weight': 5.0,
                'measure': 0, # KG
                'old_price': 120000,
                'new_price': 105000,
                'b2b_price': 100000,
                'wholesale_price': 95000,
                'min_wholesale_quantity': 5,
                'available_quantity': 50,
                'main': False
            },
            {
                'name': 'Test Guruch 25kg', 
                'weight': 25.0,
                'measure': 3, # PAKET (maybe?)
                'old_price': 600000,
                'new_price': 520000,
                'b2b_price': 500000,
                'wholesale_price': 480000,
                'min_wholesale_quantity': 2,
                'available_quantity': 20,
                'main': False
            }
        ]

        for i, data in enumerate(variants_data):
            product_item = ProductItem.objects.create(
                product_type=product_type_uuid,
                desc=data['name'], # Linking desc to name for simplicity
                desc_uz=data['name'],
                desc_ru=data['name'],
                desc_en=data['name'],
                desc_kr=data['name'],
                old_price=data['old_price'],
                new_price=data['new_price'],
                b2b_price=data['b2b_price'],
                wholesale_price=data['wholesale_price'],
                min_wholesale_quantity=data['min_wholesale_quantity'],
                weight=data['weight'],
                measure=data['measure'],
                available_quantity=data['available_quantity'],
                main=data['main'],
                active=True,
                bonus=5 # Some bonus
            )
            
            # Create Good linked to it
            Good.objects.create(
                name=data['name'],
                name_uz=data['name'],
                name_ru=data['name'],
                name_en=data['name'],
                name_kr=data['name'],
                product=product_item,
                category=category,
                ingredients='Test ingredients',
                ingredients_uz='Test ingredients',
                ingredients_ru='Test ingredients',
                ingredients_en='Test ingredients',
                ingredients_kr='Test ingredients',
                expire_date='2025-12-31'
            )
            
            self.stdout.write(f"Created ProductItem: {data['name']} (ID: {product_item.id})")

        self.stdout.write(self.style.SUCCESS('Successfully created test variants data'))
