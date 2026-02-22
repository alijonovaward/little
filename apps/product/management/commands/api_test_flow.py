from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.product.views import GoodListAPIView, GoodVariantsAPIView
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Simulate frontend API calls for verification'

    def handle(self, *args, **kwargs):
        self.stdout.write("=== Simulating Frontend Flow ===")
        
        # 1. Login
        try:
            user = User.objects.get(username="frontend_tester")
        except User.DoesNotExist:
             self.stdout.write(self.style.ERROR("User 'frontend_tester' not found! Run 'create_frontend_user' first."))
             return

        self.stdout.write(f"Logged in as: {user.username} (Is Wholesaler: {user.is_wholesaler})")

        factory = APIRequestFactory()

        # 2. Get Goods List (Oziq-ovqat
        self.stdout.write("\n--- Requesting Goods List ---")
        view = GoodListAPIView.as_view()
        # Use simple request without factory to avoid host issues if possible, or patch settings
        # Easier: Just set the SERVER_NAME in the factory
        factory = APIRequestFactory(**{'HTTP_HOST': 'localhost'})
        request = factory.get('/api/product/goods/list/')
        force_authenticate(request, user=user)
        response = view(request).render()
        
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS("Success! Found products:"))
            products = json.loads(response.content)
            
            if 'results' in products: # Pagination
                products = products['results']
                
            found_test_product = False
            test_product_type = None
            
            for item in products:
                # Check if name is in any language
                names = item.get('names', {})
                name_uz = names.get('uz', '')
                price = item.get('price', 0)
                
                self.stdout.write(f"- ID: {item.get('id')} | Name: {name_uz} | Price: {price}")
                
                if "Test Guruch" in str(name_uz):
                    found_test_product = True
                    test_product_type = item.get('product_type') # Check serializer field name for UUID
                    if not test_product_type:
                         # Fallback if serializer structure is different
                         test_product_type = item.get('product', {}).get('product_type')

                    self.stdout.write(self.style.SUCCESS("  ^^^ THIS IS THE TEST PRODUCT ^^^"))
            
            if found_test_product and test_product_type:
                 # 3. Get Variants for this product
                self.stdout.write(f"\n--- Requesting Variants for {test_product_type} ---")
                
                # Variants view expects product_type in URL
                view_variants = GoodVariantsAPIView.as_view()
                request_variants = factory.get(f'/api/product/good-variants/{test_product_type}/')
                force_authenticate(request_variants, user=user)
                response_variants = view_variants(request_variants, product_type=test_product_type).render()
                
                if response_variants.status_code == 200:
                     self.stdout.write(self.style.SUCCESS("Variants found:"))
                     variants_data = json.loads(response_variants.content)
                     
                     for v in variants_data:
                         # Structure might be nested or flat depending on serializer
                         p_data = v.get('product', {})
                         desc = p_data.get('desc', 'No Desc')
                         weight = p_data.get('weight', 0)
                         price = p_data.get('price', 0)
                         
                         self.stdout.write(f"  - Variant: {desc} | Weight: {weight}KG | Price: {price}")
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to get variants: {response_variants.status_code}"))

        else:
            self.stdout.write(self.style.ERROR(f"Failed to get goods list: {response.status_code}"))
