from django.core.management.base import BaseCommand
from apps.customer.models import Favorite, Profile
from apps.product.models import ProductItem, Category, Good
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.customer.views import FavoriteRetrieveUpdateDelete
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Verifies that Favorite Retrieve API returns full product details'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up test data...")
        
        # 1. Create User & Profile
        user, _ = User.objects.get_or_create(username='+998901234567')
        Profile.objects.get_or_create(origin=user, defaults={'full_name': 'Tester'})
        
        # 2. Create Product
        category, _ = Category.objects.get_or_create(name="Test Cat")
        product = ProductItem.objects.create(old_price=1000, new_price=900, active=True)
        Good.objects.create(product=product, category=category, name="Test Good")
        
        # 3. Create Favorite
        fav, _ = Favorite.objects.get_or_create(user=user.profile, product=product)
        
        # 4. Make Request
        factory = APIRequestFactory()
        view = FavoriteRetrieveUpdateDelete.as_view()
        
        request = factory.get(f'/api/customer/favorite/{fav.id}/retrieve/')
        force_authenticate(request, user=user)
        
        self.stdout.write("Sending GET request...")
        response = view(request, pk=fav.id)
        response.render()
        
        data = json.loads(response.content)
        product_data = data.get('product')
        
        self.stdout.write(f"Response product type: {type(product_data)}")
        self.stdout.write(f"Response product data: {product_data}")

        if isinstance(product_data, dict) and 'id' in product_data and 'desc' in product_data:
            self.stdout.write(self.style.SUCCESS("PASS: Product is a dictionary with details."))
        else:
            self.stdout.write(self.style.ERROR("FAIL: Product is NOT a dictionary (likely just an ID)."))
