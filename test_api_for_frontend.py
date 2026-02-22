import os
import django
import json
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.product.views import GoodListAPIView, GoodVariantsAPIView
from django.contrib.auth import get_user_model

User = get_user_model()

def test_frontend_flow():
    print("=== Simulating Frontend Flow ===")
    
    # 1. Login
    user = User.objects.get(username="frontend_tester")
    print(f"Logged in as: {user.username} (Is Wholesaler: {user.is_wholesaler})")

    factory = APIRequestFactory()

    # 2. Get Goods List (Oziq-ovqat)
    print("\n--- Requesting Goods List ---")
    view = GoodListAPIView.as_view()
    request = factory.get('/api/product/goods/list/')
    force_authenticate(request, user=user)
    response = view(request)
    
    if response.status_code == 200:
        print("Success! Found products:")
        products = response.data
        if 'results' in products: # Pagination
            products = products['results']
            
        found_test_product = False
        test_product_type = None
        
        for item in products:
            # Check if name is in any language
            names = item.get('names', {})
            name_uz = names.get('uz', '')
            
            print(f"- ID: {item['id']} | Name: {name_uz} | Price: {item['product']['price']}")
            
            if "Test Guruch" in name_uz:
                found_test_product = True
                test_product_type = item['product']['product_type']
                print("  ^^^ THIS IS THE TEST PRODUCT ^^^")
        
        if found_test_product and test_product_type:
             # 3. Get Variants for this product
            print(f"\n--- Requesting Variants for {test_product_type} ---")
            view_variants = GoodVariantsAPIView.as_view()
            request_variants = factory.get(f'/api/product/good-variants/{test_product_type}/')
            force_authenticate(request_variants, user=user)
            response_variants = view_variants(request_variants, product_type=test_product_type)
            
            if response_variants.status_code == 200:
                 print("Variants found:")
                 for v in response_variants.data:
                     p_data = v['product']
                     print(f"  - Variant: {p_data['desc']} | Weight: {p_data['weight']}KG | Price: {p_data['price']}")
            else:
                print(f"Failed to get variants: {response_variants.status_code}")

    else:
        print(f"Failed to get goods list: {response.status_code}")

if __name__ == "__main__":
    test_frontend_flow()
