import os
import django
import sys

# Set up Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.product.models import Category, Good, ProductItem
from apps.customer.models import Favorite, Profile
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.product.views import GoodListAPIView
from apps.customer.serializers import FavoriteSerializer

User = get_user_model()

def verify_all():
    print("\n--- FINAL VERIFICATION START ---")
    
    # 1. Test data creation
    print("Test data yaratilmoqda...")
    # Cleanup
    Good.objects.all().delete()
    ProductItem.objects.all().delete()
    Category.objects.all().delete()
    Favorite.objects.all().delete()
    
    user, _ = User.objects.get_or_create(username="verify_user")
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    cat1 = Category.objects.create(id=500, name="Filter Category", main_type="f")
    cat2 = Category.objects.create(id=501, name="Other Category", main_type="f")
    
    # Create 25 products to test pagination (page_size=20)
    for i in range(25):
        p = ProductItem.objects.create(desc=f"Product {i}", main=True, new_price=1000)
        c = cat1 if i < 10 else cat2
        Good.objects.create(name=f"Good {i}", product=p, category=c)
        if i == 0:
            Favorite.objects.create(user=user.profile, product=p)

    factory = APIRequestFactory()

    # 2. Test Pagination and Filter
    print("\n1. Test: GoodListAPIView Filter and Pagination")
    view = GoodListAPIView.as_view()
    
    # Check Filter
    request_filter = factory.get('/api/product/goods/', {'category': 500})
    request_filter.user = user
    resp_filter = view(request_filter)
    resp_filter.render()
    data_filter = resp_filter.data
    count_filter = len(data_filter.get('results', []))
    print(f"   - Category=500 filtri bo'yicha {count_filter} mahsulot topildi (Kutilgan: 10)")

    # Check Pagination (Total items = 25, page_size should be 20)
    request_pag = factory.get('/api/product/goods/')
    request_pag.user = user
    resp_pag = view(request_pag)
    resp_pag.render()
    data_pag = resp_pag.data
    page_size_found = len(data_pag.get('results', []))
    total_found = data_pag.get('count', 0)
    print(f"   - Jami mahsulotlar: {total_found}")
    print(f"   - Birinchi sahifadagi mahsulotlar soni: {page_size_found} (Kutilgan: 20)")

    # 3. Test Favorite Nested Serializer
    print("\n2. Test: Favorite Serializer Nesting")
    fav = Favorite.objects.get(user=user.profile)
    serializer = FavoriteSerializer(fav, context={'request': request_pag})
    rep = serializer.data
    is_nested = isinstance(rep.get('product'), dict)
    print(f"   - Favorite product qismi nested (dict) mi?: {is_nested}")
    if is_nested:
        print(f"   - Nested product tavsifi: {rep['product'].get('desc')}")

    print("\n--- VERIFICATION RESULT ---")
    if count_filter == 10 and page_size_found == 20 and is_nested:
        print("✅ HAMMA ISHLAR 100% TO'G'RI BAJARILGAN!")
    else:
        print("❌ QAYERDADIR XATOLIK BOR!")
    
    # Cleanup
    Good.objects.all().delete()
    ProductItem.objects.all().delete()
    Category.objects.all().delete()
    Favorite.objects.all().delete()

if __name__ == "__main__":
    verify_all()
