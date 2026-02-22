from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from apps.customer.models import Favorite
from .models import Category, Good, Image, Phone, ProductItem, Ticket
from .utils import ProductItemCreatorMixin


# --- Pagination ---
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = 'page'


# --- Mixins ---
class FavoriteMixin(metaclass=serializers.SerializerMetaclass):
    """
    is_favorite logikasini hamma joyda qayta yozmaslik uchun Mixin.
    """
    is_favorite = serializers.SerializerMethodField(read_only=True)

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        # exists() filter(...).first() dan tezroq ishlaydi
        return Favorite.objects.filter(
            user=request.user.profile,
            product=obj.product
        ).exists()


# --- Serializers ---

class CategorySerializer(serializers.ModelSerializer):
    names = serializers.SerializerMethodField()
    descriptions = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"

    def get_names(self, obj):
        return {
            "uz": getattr(obj, 'name_uz', obj.name),
            "ru": getattr(obj, 'name_ru', obj.name),
            "en": getattr(obj, 'name_en', obj.name),
            "ko": getattr(obj, 'name_ko', obj.name),
        }

    def get_descriptions(self, obj):
        return {
            "uz": getattr(obj, 'desc_uz', obj.desc),
            "ru": getattr(obj, 'desc_ru', obj.desc),
            "en": getattr(obj, 'desc_en', obj.desc),
            "ko": getattr(obj, 'desc_ko', obj.desc),
        }


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"


class ProductItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    sale = serializers.ReadOnlyField()
    descriptions = serializers.SerializerMethodField()

    class Meta:
        model = ProductItem
        fields = [
            "id", "desc", "descriptions", "product_type", "old_price", "new_price",
            "price", "sale", "weight", "measure", "available_quantity",
            "bonus", "main", "active", "created", "modified",
        ]

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None

        if user and user.is_authenticated:
            # B2B narx
            if getattr(user, "is_b2b", False) and obj.b2b_price > 0:
                return obj.b2b_price
            # Optom narx (field bo'lmasa ham xato bermasin)
            wholesale_price = getattr(obj, "wholesale_price", 0)
            if (
                getattr(user, "is_wholesaler", False)
                and getattr(user, "is_approved", False)
                and wholesale_price
                and wholesale_price > 0
            ):
                return wholesale_price
        return obj.new_price

    def get_descriptions(self, obj):
        return {
            "uz": getattr(obj, 'desc_uz', obj.desc),
            "ru": getattr(obj, 'desc_ru', obj.desc),
            "en": getattr(obj, 'desc_en', obj.desc),
            "ko": getattr(obj, 'desc_ko', obj.desc),
        }

# --- Asosiy Mahsulot Serializerlari ---

class TicketSerializer(FavoriteMixin, ProductItemCreatorMixin, serializers.ModelSerializer):
    product = ProductItemSerializer()
    names = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_names(self, obj):
        return {
            "uz": getattr(obj, 'event_name_uz', obj.event_name),
            "ru": getattr(obj, 'event_name_ru', obj.event_name),
            "en": getattr(obj, 'event_name_en', obj.event_name),
            "ko": getattr(obj, 'event_name_ko', obj.event_name),
        }

    def create(self, validated_data):
        # ProductItemCreatorMixin ichidagi create_pruduct metodiga moslab
        product_data = validated_data.pop('product')
        product = self.create_pruduct(product_data)
        return Ticket.objects.create(**validated_data, product=product)


class PhoneSerializer(FavoriteMixin, ProductItemCreatorMixin, serializers.ModelSerializer):
    product = ProductItemSerializer()
    names = serializers.SerializerMethodField()

    class Meta:
        model = Phone
        fields = "__all__"

    def get_names(self, obj):
        return {
            "uz": getattr(obj, 'model_name_uz', obj.model_name),
            "ru": getattr(obj, 'model_name_ru', obj.model_name),
            "en": getattr(obj, 'model_name_en', obj.model_name),
            "ko": getattr(obj, 'model_name_ko', obj.model_name),
        }

    def create(self, validated_data):
        product_data = validated_data.pop('product')
        product = self.create_pruduct(product_data)
        return Phone.objects.create(**validated_data, product=product)


class GoodSerializer(FavoriteMixin, ProductItemCreatorMixin, serializers.ModelSerializer):
    product = ProductItemSerializer()
    names = serializers.SerializerMethodField()
    ingredients_dict = serializers.SerializerMethodField()
    # sub_cat o'rniga category ishlatildi
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Good
        fields = "__all__"
        read_only_fields = ("images",)

    def get_names(self, obj):
        return {
            "uz": getattr(obj, 'name_uz', obj.name),
            "ru": getattr(obj, 'name_ru', obj.name),
            "en": getattr(obj, 'name_en', obj.name),
            "ko": getattr(obj, 'name_ko', obj.name),
        }

    def get_ingredients_dict(self, obj):
        return {
            "uz": getattr(obj, 'ingredients_uz', obj.ingredients),
            "ru": getattr(obj, 'ingredients_ru', obj.ingredients),
            "en": getattr(obj, 'ingredients_en', obj.ingredients),
            "ko": getattr(obj, 'ingredients_ko', obj.ingredients),
        }

    def create(self, validated_data):
        product_data = validated_data.pop('product')
        product = self.create_pruduct(product_data)
        return Good.objects.create(**validated_data, product=product)


# --- Popular va Search uchun (Inheritance ishlatamiz) ---

class TicketPopularSerializer(TicketSerializer):
    sold_count = serializers.IntegerField(read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = ["event_name", "event_date", "sold_count", "product", "is_favorite", "category"]


class PhonePopularSerializer(PhoneSerializer):
    sold_count = serializers.IntegerField(read_only=True)


class GoodPopularSerializer(GoodSerializer):
    sold_count = serializers.IntegerField(read_only=True)


# --- Variant Serializers ---

class GoodVariantSerializer(GoodSerializer):
    pass


class PhoneVariantSerializer(PhoneSerializer):
    pass


class TicketVariantSerializer(TicketSerializer):
    pass


# Search uchun alohida klass shart emas, asosiylarni o'zini ishlatsa bo'ladi
# Lekin agar maydonlar farq qilsa, yuqoridagilardan inherit qilinadi


# Variantlar uchun qisqa serializer (Masalan: faqat nomi va ID)
class VariantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='goods.name', read_only=True)

    class Meta:
        model = ProductItem
        fields = ['id', 'name', 'new_price', 'available_quantity']


class ProductVariantFullSerializer(serializers.ModelSerializer):
    names = serializers.SerializerMethodField()
    prices = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = ProductItem
        fields = [
            'id',
            'names',
            'prices',
            'images',
        ]

    def get_name(self, obj):
        names = self.get_names(obj)
        if isinstance(names, dict):
            return names.get("uz") or names.get("ru") or names.get("en") or names.get("ko")
        return None


    def get_names(self, obj):
        # Variantning turiga qarab (Good, Phone, Ticket) 4 tildagi nomini olish
        names = {"uz": "Noma'lum", "ru": "Неизвестно", "en": "Unknown", "ko": "알 수 없음"}

        # Qaysi modelga bog'langanini aniqlaymiz
        target = None
        prefix = ""
        if hasattr(obj, 'goods'):
            target = obj.goods
            prefix = "name"
        elif hasattr(obj, 'phones'):
            target = obj.phones
            prefix = "model_name"
        elif hasattr(obj, 'tickets'):
            target = obj.tickets
            prefix = "event_name"

        if target:
            names = {
                "uz": getattr(target, f"{prefix}_uz", target.name if hasattr(target, 'name') else ""),
                "ru": getattr(target, f"{prefix}_ru", ""),
                "en": getattr(target, f"{prefix}_en", ""),
                "ko": getattr(target, f"{prefix}_ko", ""),
            }
        return names


    def get_prices(self, obj):
        # Hamma narxlar va chegirma (discount) foizi
        return {
            "price": float(obj.new_price) if obj.new_price else 0,
            "b2b_price": float(obj.b2b_price) if obj.b2b_price else 0,
            "discount_percent": obj.sale,  # Modelingizdagi @property
            "min_wholesale_quantity": obj.min_wholesale_quantity,
        }

    def get_images(self, obj):
        # MUHIM: Request None bo'lsa xato bermasligi uchun tekshiruv
        request = self.context.get('request')
        images = obj.images.all()

        if request is not None:
            # Agar request bo'lsa to'liq URL: http://127.0.0.1:8000/media/...
            return [request.build_absolute_uri(img.image.url) for img in images if img.image]

        # Agar request bo'lmasa nisbiy yo'l: /media/...
        return [img.image.url for img in images if img.image]



# Asosiy mahsulot Serializeri (Hamma ma'lumotlar shu yerda)
class GoodFullSerializer(serializers.ModelSerializer):
    # ProductItem'dan narxlarni va ma'lumotlarni olamiz
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    prices = serializers.SerializerMethodField()
    names = serializers.SerializerMethodField()
    descriptions = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Good
        fields = [
            'id', 'product_id', 'names', 'descriptions', 'prices', 'images', 'variants', 'is_favorite'
        ]

    def get_names(self, obj):
        # 4 tilda nomlar
        return {
            "uz": getattr(obj, 'name_uz', obj.name),
            "ru": getattr(obj, 'name_ru', obj.name),
            "en": getattr(obj, 'name_en', obj.name),
            "ko": getattr(obj, 'name_ko', obj.name),
        }

    def get_descriptions(self, obj):
        # 4 tilda tavsiflar (ProductItem modelidagi desc maydonidan)
        p = obj.product
        return {
            "uz": getattr(p, 'desc_uz', p.desc),
            "ru": getattr(p, 'desc_ru', p.desc),
            "en": getattr(p, 'desc_en', p.desc),
            "ko": getattr(p, 'desc_ko', p.desc),
        }

    def get_prices(self, obj):
        p = obj.product if hasattr(obj, 'product') else obj  # ProductItem yoki Good ekanligini tekshirish
        request = self.context.get('request')
        user = request.user if request else None

        # Hamma uchun ko'rinadigan chakana narxlar
        prices = {
            "price": float(p.new_price) if p.new_price else 0,
            "discount_percent": p.sale,
            "min_wholesale_quantity": p.min_wholesale_quantity,
        }

        # B2B Narx validatsiyasi
        if user and user.is_authenticated and getattr(user, 'is_b2b', False):
            prices["b2b_price"] = float(p.b2b_price) if p.b2b_price else 0
        else:
            prices["b2b_price"] = None

        # Wholesale Price (Optom)
        if user and user.is_authenticated and getattr(user, 'is_wholesaler', False) and getattr(user, 'is_approved', False):
            wholesale_price = getattr(p, "wholesale_price", 0)
            prices["wholesale_price"] = float(wholesale_price) if wholesale_price else 0
        else:
            prices["wholesale_price"] = None

        return prices

    def get_images(self, obj):
        request = self.context.get('request')
        return [request.build_absolute_uri(img.image.url) for img in obj.product.images.all() if img.image]

    def get_variants(self, obj):
        queryset = (
            ProductItem.objects.filter(product_type=obj.product.product_type, active=True)
            .select_related("goods", "phones", "tickets")
            .prefetch_related("images")
            .order_by("-main", "id")
        )
        return ProductVariantFullSerializer(queryset, many=True, context=self.context).data
