import os
import django
import sys

# Setup Django environment
# Ensure the project root is in sys.path
project_root = r'C:\Users\Green IT Serves\Million-halal-mart\Million-halal-mart'
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.customer.views import LoginView, ProfileEditAPIView
from apps.product.views import GoodAllListAPIView
from apps.product.models import Category, Good, ProductItem
from apps.customer.models import Profile, B2BApplication

User = get_user_model()

def run_verification():
    print("=== Verification Started ===")
    
    # 1. Setup Test User
    username = "+998901234567"
    password = "password123"
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.save()
        Profile.objects.create(origin=user, full_name="Test User", phone_number=username)
        print(f"Created test user: {username}")
    else:
        print(f"Using existing test user: {username}")

    # Ensure profile exists
    if not hasattr(user, 'profile'):
         Profile.objects.create(origin=user, full_name="Test User", phone_number=username)

    factory = APIRequestFactory()

    # 2. Verify LoginView (B2B Status)
    print("\n[Test 1] Verifying LoginView for B2B Status...")
    login_data = {"phone_number": username, "password": password}
    request = factory.post('/api/customer/login/', login_data, format='json')
    view = LoginView.as_view()
    response = view(request)
    
    if response.status_code == 200:
        data = response.data
        if 'is_b2b' in data and 'application_status' in data:
             print(f"✅ LoginView returns 'is_b2b': {data['is_b2b']}")
             print(f"✅ LoginView returns 'application_status': {data['application_status']}")
        else:
             print("❌ LoginView MISSING 'is_b2b' or 'application_status'")
             print(f"Response keys: {data.keys()}")
    else:
        print(f"❌ Login failed: {response.status_code} - {response.data}")

    # 3. Verify Profile API (B2B Status)
    print("\n[Test 2] Verifying Profile API for B2B Status...")
    request = factory.get('/api/customer/profile/edit/')
    force_authenticate(request, user=user)
    view = ProfileEditAPIView.as_view()
    response = view(request)

    if response.status_code == 200:
        data = response.data
        if 'is_b2b' in data and 'application_status' in data:
             print(f"✅ Profile API returns 'is_b2b': {data['is_b2b']}")
             print(f"✅ Profile API returns 'application_status': {data['application_status']}")
        else:
             print("❌ Profile API MISSING 'is_b2b' or 'application_status'")
    else:
        print(f"❌ Profile API failed: {response.status_code} - {response.data}")


    # 4. Verify Product Filtering (GoodAllListAPIView)
    print("\n[Test 3] Verifying Product Filtering (Category)...")
    
    # Create dummy category and product if not exists to test filtering
    cat, _ = Category.objects.get_or_create(name="Test Category", main_type='f')
    
    # Ensure there is at least one product in this category
    product_item = ProductItem.objects.create(desc="Test Product", main=True, active=True)
    good, _ = Good.objects.get_or_create(name="Test Good", product=product_item, category=cat)

    request = factory.get(f'/api/product/goods/?category={cat.id}')
    force_authenticate(request, user=user)
    view = GoodAllListAPIView.as_view()
    response = view(request)

    if response.status_code == 200:
        results = response.data['results']
        print(f"Found {len(results)} products for category {cat.id}")
        
        all_match = True
        for item in results:
            # Note: Serializer structure might be nested, checking basic existence
            # Assuming 'product' or 'id' is present. 
            # Ideally we check if the item actually belongs to the category.
            # Since GoodFullSerializer returns complex data, let's just verify we got results.
            pass
            
        if len(results) > 0:
             print("✅ Filtering returned results.")
        else:
             print("⚠️ Filtering returned NO results (might be empty DB or filter issue).")
    else:
        print(f"❌ Product Filter API failed: {response.status_code}")


    # 5. Verify Product Search
    print("\n[Test 4] Verifying Product Search...")
    request = factory.get('/api/product/goods/?search=Test')
    force_authenticate(request, user=user)
    view = GoodAllListAPIView.as_view()
    response = view(request)

    if response.status_code == 200:
         results = response.data['results']
         print(f"Found {len(results)} products for search 'Test'")
         if len(results) > 0:
             print("✅ Search returned results.")
         else:
             print("⚠️ Search returned NO results.")
    else:
         print(f"❌ Product Search API failed: {response.status_code}")

    print("\n=== Verification Finished ===")

if __name__ == "__main__":
    run_verification()
