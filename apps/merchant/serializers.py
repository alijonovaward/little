from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from apps.product.serializers import (
    ProductItemSerializer,
)
from .models import Bonus, LoyaltyCard, Referral, LoyaltyPendingBonus
from apps.product.models import Phone, Ticket, Good
from .models import Order, OrderItem, Information, Service, SocialMedia
from ..customer.models import Profile, Location


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("total_amount", "status", "comment")


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("delivery_fee",)


class RemoveFromCartSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True, help_text="Savatning ID raqami")
    product_id = serializers.IntegerField(required=True, help_text="O'chirilishi kerak bo'lgan mahsulot ID raqami")


class OrderItemDetailsSerializer(serializers.ModelSerializer):
    product = ProductItemSerializer(read_only=True)
    product_type = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = "__all__"

    def get_product_type(self, obj):
        product_item = obj.product
        if hasattr(product_item, "phones"):
            return {
                "type": "Phone",
                "details": PhoneSerializer(product_item.phones).data,
            }
        elif hasattr(product_item, "tickets"):
            return {
                "type": "Ticket",
                "details": TicketSerializer(product_item.tickets).data,
            }
        elif hasattr(product_item, "goods"):
            return {"type": "Good", "details": GoodSerializer(product_item.goods).data}
        return None


class OrderListSerializer(serializers.ModelSerializer):
    # Status matni (Kutilmoqda, Tasdiqlandi...)
    status_display = serializers.CharField(source='get_status_display_value', read_only=True)

    # Buyurtma ichidagi mahsulotlar (4 tildagi ma'lumotlar bilan)
    products_details = serializers.SerializerMethodField()

    # User va Manzil ma'lumotlari
    customer_name = serializers.ReadOnlyField(source='user.full_name')
    address = serializers.ReadOnlyField(source='location.address')

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'customer_name',
            'address',
            'total_amount',
            'delivery_fee',
            'bonus_amount',
            'loyalty_payment',
            'comment',
            'products_details',
            'created_at'
        ]

    def get_products_details(self, obj):
        request = self.context.get('request')
        result = []

        for item in obj.orderitem.all():
            p = item.product  # ProductItem obyekti
            if p:
                # 1. Mahsulot nomlarini 4 tilda yig'amiz
                names = {"uz": "Noma'lum", "ru": "Неизвестно", "en": "Unknown", "ko": "알 수 없음"}

                if hasattr(p, 'phones'):
                    names = {
                        "uz": getattr(p.phones, 'model_name_uz', p.phones.model_name),
                        "ru": getattr(p.phones, 'model_name_ru', p.phones.model_name),
                        "en": getattr(p.phones, 'model_name_en', p.phones.model_name),
                        "ko": getattr(p.phones, 'model_name_ko', p.phones.model_name),
                    }
                elif hasattr(p, 'goods'):
                    names = {
                        "uz": getattr(p.goods, 'name_uz', p.goods.name),
                        "ru": getattr(p.goods, 'name_ru', p.goods.name),
                        "en": getattr(p.goods, 'name_en', p.goods.name),
                        "ko": getattr(p.goods, 'name_ko', p.goods.name),
                    }
                elif hasattr(p, 'tickets'):
                    names = {
                        "uz": getattr(p.tickets, 'event_name_uz', p.tickets.event_name),
                        "ru": getattr(p.tickets, 'event_name_ru', p.tickets.event_name),
                        "en": getattr(p.tickets, 'event_name_en', p.tickets.event_name),
                        "ko": getattr(p.tickets, 'event_name_ko', p.tickets.event_name),
                    }

                # 2. Tavsiflarni (ProductItem modelidagi desc) 4 tilda yig'amiz
                descriptions = {
                    "uz": getattr(p, 'desc_uz', p.desc),
                    "ru": getattr(p, 'desc_ru', p.desc),
                    "en": getattr(p, 'desc_en', p.desc),
                    "ko": getattr(p, 'desc_ko', p.desc),
                }

                # 3. Mahsulot rasmlarini to'liq URL bilan olish
                images = []
                for img_obj in p.images.all():
                    if img_obj.image:
                        full_url = request.build_absolute_uri(img_obj.image.url) if request else img_obj.image.url
                        images.append(full_url)

                # 4. Barcha ma'lumotlarni yig'ish
                result.append({
                    "id": p.id,
                    "names": names,  # 4 tildagi nomlar
                    "quantity": item.quantity,
                    "price": float(p.new_price or p.old_price),
                    "total_price": float((p.new_price or p.old_price) * item.quantity),
                    "measure": p.get_measure_display(),
                    "images": images,
                    "descriptions": descriptions  # 4 tildagi tavsiflar
                })
        return result


class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"

    def create(self, validated_data):
        # Bu qism faqat CreateAPIView da ishlaydi (yangi qo'shishda)
        user = self.context["request"].user
        product = validated_data.get("product")
        order, created = Order.objects.get_or_create(
            user=user.profile, status="in_cart"
        )
        validated_data["order"] = order

        order_item, item_created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={"quantity": validated_data.get("quantity", 0)},
        )
        if not item_created:
            order_item.quantity += validated_data.get("quantity", 0)
            order_item.save()
        order.update_total_amount()
        return order_item


class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = "__all__"


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = "__all__"


class OrderItemListSerializer(serializers.ModelSerializer):
    product = ProductItemSerializer(read_only=True)
    product_type = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = "__all__"

    def get_product_type(self, obj):
        product_item = obj.product
        if hasattr(product_item, "phones"):
            return {
                "type": "Phone",
                "details": PhoneSerializer(product_item.phones).data,
            }
        elif hasattr(product_item, "tickets"):
            return {
                "type": "Ticket",
                "details": TicketSerializer(product_item.tickets).data,
            }
        elif hasattr(product_item, "goods"):
            return {"type": "Good", "details": GoodSerializer(product_item.goods).data}
        return None


class InformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Information
        fields = "__all__"


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status", "comment", "location"]

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.comment = validated_data.get("comment", instance.comment)
        instance.location = validated_data.get("location", instance.location)
        instance.save()
        return instance


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = "__all__"


class BonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bonus
        fields = "__all__"


class LoyaltyCardSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)

    class Meta:
        model = LoyaltyCard
        fields = [
            'id',
            'profile',  # id профиля
            'full_name',  # имя пользователя
            'current_balance',
            'cycle_start',
            'cycle_end',
            'cycle_days',
            'cycle_number',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'full_name', 'created_at', 'updated_at']


class MyReferralHistorySerializer(serializers.ModelSerializer):
    friend_name = serializers.CharField(source='referee.full_name', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Referral
        fields = ['friend_name', 'status', 'created_at']


class UserBonusSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    my_referrals_list = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'full_name', 'referral_code', 'balance', 'my_referrals_list']

    def get_balance(self, obj):
        try:
            return obj.loyalty_card.current_balance
        except:
            return 0

    def get_my_referrals_list(self, obj):
        invites = Referral.objects.filter(referrer=obj).order_by('-created_at')
        return MyReferralHistorySerializer(invites, many=True).data


class CartAddSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField()


class CheckoutSerializer(serializers.Serializer):
    # Bu maydon ID qabul qiladi (masalan: 5), lekin bizga Location obyektini beradi
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    comment = serializers.CharField(required=False, allow_blank=True)


class ReceiptUploadSerializer(serializers.Serializer):
    order_number = serializers.CharField(
        max_length=50,
        help_text="Buyurtma raqamini kiriting (masalan: ORD123...)"
    )
    payment_receipt = serializers.FileField(
        help_text="To'lov cheki rasmi yoki PDF faylini yuklang"
    )


# 4. Buyurtma tafsilotlari (Rasmda ko'ringan Timeline bilan)
class OrderDetailSerializer(serializers.ModelSerializer):
    bank_card_number = serializers.ReadOnlyField(source='bankcard.title')
    bank_card_holder = serializers.ReadOnlyField(source='bankcard.card_holder')

    # Karta raqamini chiroyli formatda chiqarish: 8600 1234 5678 9012
    formatted_card_number = serializers.SerializerMethodField()

    timeline = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    customer_name = serializers.ReadOnlyField(source='user.full_name')
    location_address = serializers.ReadOnlyField(source='location.address')

    class Meta:
        model = Order
        # 1. BU YERDAN name_uz, description_uz VA BOSHQA NOTOG'RI FIELDLARNI OLIB TASHLADIK
        fields = [
            'id', 'order_number', 'status', 'customer_name',
            'location_address', 'total_amount', 'delivery_fee',
            'bonus_amount', 'loyalty_payment', 'bank_card_number', 'bank_card_holder', 'formatted_card_number',
            'comment', 'created_at', 'timeline', 'items'
        ]

    def get_formatted_card_number(self, obj) -> str:
        # Karta biriktirilganligini tekshiramiz
        if obj.bankcard and obj.bankcard.title:
            card_str = str(obj.bankcard.title)
            # Har 4 ta raqamdan keyin probel qo'shish
            return " ".join([card_str[i:i + 4] for i in range(0, len(card_str), 4)])
        return "Karta biriktirilmagan"

    def get_items(self, obj):
        request = self.context.get('request')
        result = []

        for item in obj.orderitem.all():
            p = item.product  # ProductItem obyekti
            if p:
                # 2. Mahsulot nomlarini 4 tilda yig'amiz (Phone, Good yoki Ticket bo'lishiga qarab)
                names = {"uz": "Noma'lum", "ru": "Неизвестно", "en": "Unknown", "ko": "알 수 없음"}

                if hasattr(p, 'phones'):
                    names = {
                        "uz": getattr(p.phones, 'model_name_uz', p.phones.model_name),
                        "ru": getattr(p.phones, 'model_name_ru', p.phones.model_name),
                        "en": getattr(p.phones, 'model_name_en', p.phones.model_name),
                        "ko": getattr(p.phones, 'model_name_ko', p.phones.model_name),
                    }
                elif hasattr(p, 'goods'):
                    names = {
                        "uz": getattr(p.goods, 'name_uz', p.goods.name),
                        "ru": getattr(p.goods, 'name_ru', p.goods.name),
                        "en": getattr(p.goods, 'name_en', p.goods.name),
                        "ko": getattr(p.goods, 'name_ko', p.goods.name),
                    }
                elif hasattr(p, 'tickets'):
                    names = {
                        "uz": getattr(p.tickets, 'event_name_uz', p.tickets.event_name),
                        "ru": getattr(p.tickets, 'event_name_ru', p.tickets.event_name),
                        "en": getattr(p.tickets, 'event_name_en', p.tickets.event_name),
                        "ko": getattr(p.tickets, 'event_name_ko', p.tickets.event_name),
                    }

                # 3. Mahsulot tavsifini (desc) 4 tilda olamiz
                descriptions = {
                    "uz": getattr(p, 'desc_uz', p.desc),
                    "ru": getattr(p, 'desc_ru', p.desc),
                    "en": getattr(p, 'desc_en', p.desc),
                    "ko": getattr(p, 'desc_ko', p.desc),
                }

                # 4. Rasmlarni to'liq URL bilan olish
                product_images = [request.build_absolute_uri(img.image.url) for img in p.images.all() if img.image]

                result.append({
                    "product_id": p.id,
                    "names": names,  # 4 ta tilda nomlar shu yerda
                    "quantity": item.quantity,
                    "price": float(p.new_price or p.old_price),
                    "total_item_price": float((p.new_price or p.old_price) * item.quantity),
                    "images": product_images,
                    "measure": p.get_measure_display(),
                    "descriptions": descriptions  # 4 ta tilda tavsiflar shu yerda
                })
        return result

    def get_timeline(self, obj):
        is_receipt_uploaded = bool(obj.payment_receipt)
        return {
            "step1_created": True,
            "step1_date": obj.created_at,
            "step2_paid": is_receipt_uploaded or obj.status in ['approved', 'sent'],
            "step3_approved": obj.status in ['approved', 'sent'],
            "current_status": obj.get_status_display_value()
        }


class OrderReceiptUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["payment_receipt"]


class LoyaltySpendingHistorySerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="spending")  # Flutterchi farqlashi uchun

    class Meta:
        model = Order
        fields = ['order_number', 'loyalty_payment', 'status', 'created_at', 'type']


# 2. Shaxsiy zakazdan kelgan cashback (Kirim)
class LoyaltyEarnedHistorySerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="cashback")
    order_number = serializers.ReadOnlyField(source='order.order_number')

    class Meta:
        model = LoyaltyPendingBonus
        fields = ['order_number', 'order_amount', 'percent', 'bonus_amount', 'status', 'created_at', 'type']


# 3. Referaldan kelgan bonus (Kirim)
class ReferralHistorySerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="referral")
    friend_name = serializers.ReadOnlyField(source='referee.full_name')
    bonus_amount = serializers.ReadOnlyField(default=5000)  # Siz aytgan 5000 won

    class Meta:
        model = Referral
        fields = ['friend_name', 'bonus_amount', 'status', 'created_at', 'type']


# 4. UMUMIY HISTORY (Hamma ma'lumotlarni bitta Response ichida qaytarish uchun)
class LoyaltyFullHistorySerializer(serializers.Serializer):
    current_balance = serializers.DecimalField(max_digits=20, decimal_places=0)
    spending_history = LoyaltySpendingHistorySerializer(many=True)
    cashback_history = LoyaltyEarnedHistorySerializer(many=True)
    referral_history = ReferralHistorySerializer(many=True)


class CartUpdateQuantitySerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True, help_text="Buyurtmaning (Order) ID raqami")
    product_id = serializers.IntegerField(required=True, help_text="Mahsulotning (ProductItem) ID raqami")
    quantity = serializers.IntegerField(min_value=0, help_text="Yangi miqdor (0 bo'lsa o'chadi)")



class B2BStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="STANDARD, WAITING, yoki B2B_MEMBER")
    message = serializers.CharField()
    is_wholesaler = serializers.BooleanField()
    is_approved = serializers.BooleanField()
