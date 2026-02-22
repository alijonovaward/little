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

def clear_and_seed():
    print("Clearing database...")
    with transaction.atomic():
        Good.objects.all().delete()
        Image.objects.all().delete()
        Category.objects.all().delete()
        ProductItem.objects.all().delete()
        print("Database cleared.")

        # 1. Categories
        print("Creating Categories...")
        categories = {
            "meva": Category.objects.create(name_uz="Mevalar", name_ru="Фрукты", name_en="Fruits", name_ko="과일", main_type="f"),
            "sabzavot": Category.objects.create(name_uz="Sabzavotlar", name_ru="Овощи", name_en="Vegetables", name_ko="야채", main_type="f"),
            "sut": Category.objects.create(name_uz="Sut mahsulotlari", name_ru="Молочные продукты", name_en="Dairy", name_ko="유제품", main_type="f"),
            "non": Category.objects.create(name_uz="Non va qandolat", name_ru="Хлеб и выпечка", name_en="Bakery", name_ko="베이커리", main_type="f"),
            "gosht": Category.objects.create(name_uz="Go'sht mahsulotlari", name_ru="Мясные продукты", name_en="Meat Products", name_ko="육류 제품", main_type="f"),
            "ichimlik": Category.objects.create(name_uz="Ichimliklar", name_ru="Напитки", name_en="Drinks", name_ko="음료", main_type="f"),
            "shirinlik": Category.objects.create(name_uz="Shirinliklar", name_ru="Сладости", name_en="Sweets", name_ko="사탕", main_type="f"),
        }

        def add_good(cat, names, price, expire_days=30):
            desc_uz = f"{names['uz']} - Yangi va mazali mahsulot. Sog'liq uchun foydali va sifatli."
            desc_ru = f"{names['ru']} - Свежий и вкусный продукт. Полезный для здоровья и качественный."
            desc_en = f"{names['en']} - Fresh and tasty product. Healthy and high quality."
            desc_ko = f"{names['ko']} - 신선하고 맛있는 제품입니다. 건강하고 품질이 좋습니다."
            
            pi = ProductItem.objects.create(
                desc_uz=desc_uz, desc_ru=desc_ru, desc_en=desc_en, desc_ko=desc_ko,
                new_price=price, old_price=price + 1000, available_quantity=100, main=True, active=True
            )
            Good.objects.create(
                product=pi, category=cat,
                name_uz=names['uz'], name_ru=names['ru'], name_en=names['en'], name_ko=names['ko'],
                expire_date=date.today() + timedelta(days=expire_days)
            )

        # 2. SEED DATA
        print("Adding data...")

        # Fruits (10)
        fruit_data = [
            ({"uz": "Mango", "ru": "Манго", "en": "Mango", "ko": "망고"}, 5000),
            ({"uz": "Ananas", "ru": "Ананас", "en": "Pineapple", "ko": "파인애플"}, 4000),
            ({"uz": "Avokado", "ru": "Авокадо", "en": "Avocado", "ko": "아보카도"}, 3000),
            ({"uz": "Anor", "ru": "Гранат", "en": "Pomegranate", "ko": "석류"}, 4500),
            ({"uz": "Kivi", "ru": "Киви", "en": "Kiwi", "ko": "키위"}, 2500),
            ({"uz": "Olma", "ru": "Яблоко", "en": "Apple", "ko": "사과"}, 2000),
            ({"uz": "Banan", "ru": "Банан", "en": "Banana", "ko": "바나나"}, 3500),
            ({"uz": "Uzum", "ru": "Виноград", "en": "Grape", "ko": "포도"}, 6000),
            ({"uz": "Shaftoli", "ru": "Персик", "en": "Peach", "ko": "복숭아"}, 5500),
            ({"uz": "O'rik", "ru": "Абрикос", "en": "Apricot", "ko": "살구"}, 4000),
        ]
        for n, p in fruit_data: add_good(categories['meva'], n, p)

        # Vegetables (10)
        veg_data = [
            ({"uz": "Bodring", "ru": "Огурец", "en": "Cucumber", "ko": "오이"}, 1500),
            ({"uz": "Pomidor", "ru": "Помидор", "en": "Tomato", "ko": "토마토"}, 2000),
            ({"uz": "Kartoshka", "ru": "Картофель", "en": "Potato", "ko": "감자"}, 1200),
            ({"uz": "Piyoz", "ru": "Лук", "en": "Onion", "ko": "양파"}, 1000),
            ({"uz": "Sabzi", "ru": "Морковь", "en": "Carrot", "ko": "당근"}, 1300),
            ({"uz": "Baqlajon", "ru": "Баклажан", "en": "Eggplant", "ko": "가지"}, 1800),
            ({"uz": "Qalampir", "ru": "Перец", "en": "Pepper", "ko": "고추"}, 2500),
            ({"uz": "Karam", "ru": "Капуста", "en": "Cabbage", "ko": "양배추"}, 1100),
            ({"uz": "Sarimsoq", "ru": "Чеснок", "en": "Garlic", "ko": "마늘"}, 5000),
            ({"uz": "Kashnich", "ru": "Кориандр", "en": "Coriander", "ko": "고수"}, 800),
        ]
        for n, p in veg_data: add_good(categories['sabzavot'], n, p)

        # Dairy (5)
        dairy_data = [
            ({"uz": "Sut", "ru": "Молоко", "en": "Milk", "ko": "우유"}, 2500),
            ({"uz": "Qatiq", "ru": "Кефир", "en": "Kefir", "ko": "케피어"}, 2000),
            ({"uz": "Sariyog'", "ru": "Сливочное масло", "en": "Butter", "ko": "버터"}, 8000),
            ({"uz": "Pishloq", "ru": "Сыр", "en": "Cheese", "ko": "치즈"}, 12000),
            ({"uz": "Qaymoq", "ru": "Сливки", "en": "Cream", "ko": "크림"}, 5000),
        ]
        for n, p in dairy_data: add_good(categories['sut'], n, p, 7)

        # Bakery (5)
        bakery_data = [
            ({"uz": "Non", "ru": "Хлеб", "en": "Bread", "ko": "빵"}, 3000),
            ({"uz": "Patir", "ru": "Лепешка", "en": "Flatbread", "ko": "플랫브레드"}, 5000),
            ({"uz": "Buxanka", "ru": "Буханка", "en": "Loaf", "ko": "덩어리"}, 2500),
            ({"uz": "Pechenye", "ru": "Печенье", "en": "Cookies", "ko": "쿠키"}, 15000),
            ({"uz": "Bulochka", "ru": "Булочка", "en": "Bun", "ko": "번"}, 4000),
        ]
        for n, p in bakery_data: add_good(categories['non'], n, p, 3)

        # Drinks (5)
        drink_data = [
            ({"uz": "Suv", "ru": "Вода", "en": "Water", "ko": "물"}, 1000),
            ({"uz": "Sharbat", "ru": "Сок", "en": "Juice", "ko": "주스"}, 3500),
            ({"uz": "Cola", "ru": "Кола", "en": "Cola", "ko": "콜라"}, 4000),
            ({"uz": "Choy", "ru": "Чай", "en": "Tea", "ko": "차"}, 2000),
            ({"uz": "Kofe", "ru": "Кофе", "en": "Coffee", "ko": "커피"}, 8000),
        ]
        for n, p in drink_data: add_good(categories['ichimlik'], n, p, 180)

    print("Success! 40+ dynamic items added to Neon.")

if __name__ == "__main__":
    clear_and_seed()
