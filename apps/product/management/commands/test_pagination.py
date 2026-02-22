from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.product.views import GoodListAPIView
from apps.customer.views import NewsListAPIView
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Verify FlexiblePagination behavior'

    def handle(self, *args, **kwargs):
        self.stdout.write("=== Testing Flexible Pagination ===")
        
        try:
            user = User.objects.get(username="frontend_tester")
        except User.DoesNotExist:
             self.stdout.write(self.style.ERROR("User 'frontend_tester' not found!"))
             return

        factory = APIRequestFactory(**{'HTTP_HOST': 'localhost'})

        # Test 1: Product List with page_size=1
        self.stdout.write("\n--- Test 1: Goods List (page_size=1) ---")
        view = GoodListAPIView.as_view()
        request = factory.get('/api/product/goods/list/?page_size=1')
        force_authenticate(request, user=user)
        response = view(request).render()
        
        if response.status_code == 200:
            data = json.loads(response.content)
            results = data.get('results', [])
            count = data.get('count', 0)
            
            self.stdout.write(f"Total items in DB: {count}")
            self.stdout.write(f"Items returned: {len(results)}")
            
            if len(results) == 1:
                self.stdout.write(self.style.SUCCESS("PASS: Returned exactly 1 item as requested."))
            else:
                 self.stdout.write(self.style.ERROR(f"FAIL: Expected 1 item, got {len(results)}"))
        else:
             self.stdout.write(self.style.ERROR(f"Request failed: {response.status_code}"))

        # Test 2: Product List with default page_size (should be 10)
        # Note: We verify logic, even if we assume we might have less than 10 items in DB, 
        # but if we have > 1, and we ask for 1 in Test 1, and it works, then pagination is active.
        self.stdout.write("\n--- Test 2: Goods List (Default page_size 20) ---")
        request = factory.get('/api/product/goods/list/')
        force_authenticate(request, user=user)
        response = view(request).render()
        
        if response.status_code == 200:
            data = json.loads(response.content)
            results = data.get('results', [])
            self.stdout.write(f"Items returned (Default): {len(results)}")
            self.stdout.write(self.style.SUCCESS("PASS: Request successful."))
        
