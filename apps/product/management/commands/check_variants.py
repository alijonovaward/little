from django.core.management.base import BaseCommand
from apps.product.models import ProductItem, Good

class Command(BaseCommand):
    help = 'Verify test data'

    def handle(self, *args, **kwargs):
        goods = Good.objects.filter(category__name='Oziq-ovqat Test')
        self.stdout.write(f"Found {goods.count()} test goods.")
        
        for good in goods:
            p = good.product
            variants = p.variants
            self.stdout.write(f"Good: {good.name} (ID: {good.id}) -> Product: {p.id}")
            self.stdout.write(f"ProductType: {p.product_type}")
            self.stdout.write(f"Variants count: {variants.count()}")
            if variants.count() > 0:
                self.stdout.write("Variants populated correctly.")
