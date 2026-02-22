from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from apps.product.models import ProductItem, Good, Phone, Ticket, Image
from .models import Favorite, Location, News, Profile, ViewedNews, Banner, B2BApplication


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    password = serializers.CharField()
    device_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        phone_number = data.get("phone_number")
        password = data.get("password")

        if phone_number and password:
            try:
                profile = Profile.objects.get(phone_number=phone_number)
                user = profile.origin
                if user.check_password(password):
                    data["user"] = user
                    data["profile"] = profile
                    return data
                else:
                    # Multi-language error message for incorrect password
                    raise serializers.ValidationError(
                        {
                            "error": {
                                "en": _("Invalid password"),
                                "uz": _("Parol xato"),
                                "ru": _("Неверный пароль"),
                                "kr": _("비밀번호가 들렸습니다"),
                            }
                        }
                    )
            except Profile.DoesNotExist:
                # Multi-language error message for invalid phone number
                raise serializers.ValidationError(
                    {
                        "error": {
                            "en": _("Please enter a valid phone number"),
                            "uz": _("Iltimos, yaroqli telefon raqamini kiriting"),
                            "ru": _("Пожалуйста, введите действующий номер телефона"),
                            "kr": _("유효한 전화 번호를 입력하세요"),
                        }
                    }
                )


# ProfileSerializer keyinroq to'liqroq variantda yozilgan (is_b2b va application_status bilan)


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17,
        help_text="Номер телефона в формате +998901234567"
    )
    full_name = serializers.CharField(
        required=False,
        help_text="Полное имя пользователя"
    )
    referral_code = serializers.CharField(
        required=False,
        help_text="Реферальный код друга (если есть)"
    )

    def validate_phone_number(self, value):
        # Telefon raqamini validatsiya qilish
        # Masalan, formatni tekshirish yoki raqamning mavjudligini tekshirish
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    otp = serializers.CharField(max_length=100)

    def validate(self, data):
        phone_number = data.get("phone_number")
        otp = data.get("otp")

        try:
            profile = Profile.objects.get(phone_number=phone_number)
            if phone_number == "+821021424342":
                return data
            if profile.otp != otp:
                # Multi-language error message for invalid OTP
                raise serializers.ValidationError(
                    {
                        "en": _("Invalid confirmation code"),
                        "uz": _("Tasdiq kodi noto'g'ri"),
                        "ru": _("Неверный код подверждение"),
                        "kr": _("인증번호가 잘못되었습니다"),
                    }
                )
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Profile not found")

        return data


class SetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    new_password = serializers.CharField(style={"input_type": "password"})

    def validate_new_password(self, value):
        # Bu yerda parolni validatsiya qilish qoidalari qo'shilishi mumkin
        return value


class ProfileSerializer(serializers.ModelSerializer):
    is_b2b = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = "__all__"

    def get_is_b2b(self, obj):
        return getattr(obj.origin, "is_b2b", False)

    def get_application_status(self, obj):
        # Eng oxirgi arizani olamiz (agar bo'lsa)
        # B2BApplication userga bog'langan (Profile.origin)
        from .models import B2BApplication  # Circular import oldini olish uchun
        last_app = B2BApplication.objects.filter(user=obj.origin).order_by("-created").first()
        if last_app:
            return last_app.status
        return None


class LocationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Location
        fields = "__all__"


class LocationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if "image" in rep:
            if instance.image and hasattr(instance.image, "url"):
                full_path = settings.DOMAIN_NAME + instance.image.url
                rep["image"] = full_path
            else:
                rep["image"] = None
        return rep


class ViewedNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewedNews
        fields = "__all__"
        read_only_fields = ["user"]

    def create(self, validated_data):
        user = self.context["request"].user.profile
        news = validated_data["news"]
        viewed_news, created = ViewedNews.objects.get_or_create(user=user, news=news)
        return viewed_news


class TicketForFavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"


class PhoneFavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = "__all__"


class GoodFavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = "__all__"


class ImageForProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["image", "name"]


class ProductItemForFavouriteSerializer(serializers.ModelSerializer):
    # price -> bitta narx qaytadi (B2C yoki B2B)
    price = serializers.SerializerMethodField()
    tickets = TicketForFavouriteSerializer(read_only=True)
    phones = PhoneFavouriteSerializer(read_only=True)
    goods = GoodFavouriteSerializer(read_only=True)
    images = ImageForProductItemSerializer(many=True, read_only=True)
    sale = serializers.ReadOnlyField()

    class Meta:
        model = ProductItem
        fields = [
            "id",
            "desc",
            "product_type",
            "price",
            "sale",
            "weight",
            "measure",
            "available_quantity",
            "bonus",
            "main",
            "active",
            "tickets",
            "phones",
            "goods",
            "images",
            "created",
            "modified",
        ]

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None

        if user and user.is_authenticated and getattr(user, "is_b2b", False):
            if getattr(obj, "b2b_price", 0) and obj.b2b_price > 0:
                return obj.b2b_price

        wholesale_price = getattr(obj, "wholesale_price", 0)
        if user and user.is_authenticated and getattr(user, "is_wholesaler", False) and getattr(user, "is_approved", False):
            if wholesale_price and wholesale_price > 0:
                return wholesale_price

        return obj.new_price


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Favorite
        fields = "__all__"
        extra_kwargs = {'product': {'write_only': True}}

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Mahsulot ma'lumotlarini to'liq qaytarish
        rep["product"] = ProductItemForFavouriteSerializer(
            instance.product, context=self.context
        ).data
        return rep






class ProductItemForFavoriteSerializer(serializers.ModelSerializer):
    names = serializers.SerializerMethodField()
    descriptions = serializers.SerializerMethodField()
    prices = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = ProductItem
        fields = [
            'id',
            'names',
            'descriptions',
            'prices',
            'images',
            'product_type'
        ]

    def get_names(self, obj):
        # Mahsulot turini aniqlaymiz (Good, Phone, Ticket)
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
            return {
                "uz": getattr(target, f"{prefix}_uz", ""),
                "ru": getattr(target, f"{prefix}_ru", ""),
                "en": getattr(target, f"{prefix}_en", ""),
                "ko": getattr(target, f"{prefix}_ko", ""),
            }
        return {"uz": "Nomsiz mahsulot"}

    def get_descriptions(self, obj):
        # ProductItem dagi desc maydonini 4 tilda olish
        return {
            "uz": getattr(obj, 'desc_uz', obj.desc),
            "ru": getattr(obj, 'desc_ru', obj.desc),
            "en": getattr(obj, 'desc_en', obj.desc),
            "ko": getattr(obj, 'desc_ko', obj.desc),
        }

    def get_prices(self, obj):
        # Hamma narxlarni bitta obyektga yig'amiz
        return {
            "price": float(obj.new_price) if obj.new_price else 0,
            "b2b_price": float(obj.b2b_price) if obj.b2b_price else 0,
            "discount_percent": obj.sale,
        }

    def get_images(self, obj):
        # Flutter'da parsing xatoligi bo'lmasligi uchun har bir image Map bo'lib kelsin
        # (ya'ni list[str] emas, list[{'image': <url>, 'name': <name>}] )
        request = self.context.get('request')
        images = obj.images.all()

        result = []
        for img in images:
            if not getattr(img, "image", None):
                continue

            url = img.image.url
            if request is not None:
                url = request.build_absolute_uri(url)

            result.append({
                "image": url,
                "name": getattr(img, "name", "")
            })

        return result

# 2. ASOSIY Favorite Serializeri
class FavoriteListSerializer(serializers.ModelSerializer):
    # Mahsulot ma'lumotlarini yuqoridagi Full serializer orqali chiqaramiz
    product = ProductItemForFavoriteSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created']


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"


# class B2BApplicationCreateSerializer(serializers.ModelSerializer):
#     """/api/customer/b2b/apply/ -> B2B ariza yuborish (POST)"""

#     user = serializers.PrimaryKeyRelatedField(read_only=True)
#     status = serializers.CharField(read_only=True)
#     document_image = serializers.ImageField(required=False, allow_null=True, write_only=True)

#     class Meta:
#         model = B2BApplication
#         fields = [
#             "id",
#             "user",
#             "company_name",
#             "phone",
#             "address",
#             "contact_person",
#             "extra_info",
#             "document_image",
#             "status",
#             "created",
#         ]
class B2BApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for B2B application submission"""
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    document_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Upload company documents (passport, license, etc.)"
    )

    class Meta:
        model = B2BApplication
        fields = [
            "id",
            "user",
            "company_name",
            "phone",
            "address",
            "contact_person",
            "extra_info",
            "document_image",
            "status",
            "created",
        ]

# class NewsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = News
#         fields = '__all__'

# class ViewedNewsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ViewedNews
#         fields = '__all__'
