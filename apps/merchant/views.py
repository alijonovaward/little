from urllib import request
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView, RetrieveAPIView, GenericAPIView,
)
from django.utils.translation import gettext_lazy as _
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, permissions, parsers
from django.db import transaction
from django.db.models import Prefetch, F
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.product.models import Image, ProductItem
from .models import Order, OrderItem, Information, Service, SocialMedia, Bonus, LoyaltyCard, Referral, \
    LoyaltyPendingBonus, BankCardModel
from .serializers import (
    CustomPageNumberPagination,
    OrderItemSerializer,
    OrderSerializer,
    InformationSerializer,
    OrderStatusUpdateSerializer,
    ServiceSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    SocialMediaSerializer,
    BonusSerializer, LoyaltyCardSerializer, UserBonusSerializer, CartAddSerializer,
    CheckoutSerializer, ReceiptUploadSerializer, OrderDetailSerializer, LoyaltySpendingHistorySerializer,
    LoyaltyEarnedHistorySerializer, ReferralHistorySerializer, CartUpdateQuantitySerializer, RemoveFromCartSerializer,
    B2BStatusResponseSerializer,
)
from apps.dashboard.main import bot


# Create your views here.


class B2BStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Merchant"],
        summary="Foydalanuvchining B2B statusini ko'rish",
        responses={200: B2BStatusResponseSerializer}
    )
    def get(self, request):
        user = request.user
        is_approved = getattr(user, "is_approved", False)
        is_wholesaler = getattr(user, "is_wholesaler", False)

        # 1. B2B_MEMBER - Ham wholesaler, ham admin tasdiqlagan
        if is_approved and is_wholesaler:
            status_code = "B2B_MEMBER"
            message = "Tabriklaymiz! Siz tasdiqlangan B2B hamkorsiz. Barcha optom narxlar sizga ochiq."

        # 2. WAITING - Wholesaler tugmasini bosgan, lekin admin hali tasdiqlamagan
        elif is_wholesaler and not is_approved:
            status_code = "WAITING"
            message = "Sizning B2B so'rovingiz yuborilgan. Admin tasdiqlashini kuting."

        # 3. STANDARD - Oddiy user
        else:
            status_code = "STANDARD"
            message = "Siz hozircha oddiy foydalanuvchisiz."

        return Response({
            "status": status_code,
            "message": message,
            "is_wholesaler": is_wholesaler,
            "is_approved": is_approved,
        })


@extend_schema(tags=["Savatdan mahsulotni o'chirish"])
class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RemoveFromCartSerializer

    @extend_schema(
        summary="Savatdan mahsulotni o'chirish (Order ID va Product ID orqali)",
        request=RemoveFromCartSerializer,
        responses={200: {"message": "object"}, 404: "Topilmadi"}
    )
    def post(self, request):
        # 1. Ma'lumotlarni serializer orqali tekshiramiz
        serializer = RemoveFromCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_profile = request.user.profile
        order_id = serializer.validated_data.get("order_id")
        product_id = serializer.validated_data.get("product_id")

        # 2. Foydalanuvchining aynan shu 'in_cart' statusidagi buyurtmasini topamiz
        order = get_object_or_404(
            Order,
            id=order_id,
            user=user_profile,
            status='in_cart'
        )

        # 3. Buyurtma ichidan kerakli mahsulotni (OrderItem) topamiz
        order_item = OrderItem.objects.filter(
            order=order,
            product_id=product_id
        ).first()

        if not order_item:
            return Response(
                {"detail": "Ushbu mahsulot savatda topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4. O'chirish va savat summasini yangilash
        order_item.delete()
        order.update_total_amount()

        # 5. Muvaffaqiyatli xabarlar
        success_message = {
            "uz": "Maxsulot savatdan o'chirib tashlandi",
        }

        return Response({
            "message": success_message,
            "total_amount": order.total_amount  # Yangilangan summani ham qaytarish foydali
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Merchant"])
class OrderCreateAPIView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if (
                serializer.validated_data.get("status") == "in_cart"
                and Order.objects.filter(user=request.user, status="in_cart").exists()
        ):
            return Response(
                {"detail": "You already have an in-cart order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


@extend_schema(tags=["Status boycha API"])
class OrderListAPIView(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["user__full_name"]
    filterset_fields = ["user__full_name", "status"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Bu metod faqat autentifikatsiya qilingan foydalanuvchiga tegishli orderlarni qaytaradi.
        """
        user = self.request.user
        if user.is_anonymous:
            return Order.objects.none()

        # Efficiently prefetching related data
        # product_prefetch = Prefetch(
        #     'products',
        #     queryset=ProductItem.objects.all()
        #     .select_related('phones', 'tickets', 'goods')  # Optimize OneToOne relations
        #     .prefetch_related(
        #         Prefetch('images', queryset=Image.objects.all(), to_attr='prefetched_images')
        #     )
        # )

        # return (
        #     Order.objects.filter(user=user.profile)
        #     .prefetch_related(
        #         product_prefetch,  # Products with optimized related objects
        #         'orderitem', # Order items linked to the order
        #         'orderitem__product'
        #     )
        #     .order_by("-created")  # Most recent orders first
        # )

        product_prefetch = Prefetch(
            'product',
            queryset=ProductItem.objects.all()
            .select_related('phones', 'tickets', 'goods')
            .prefetch_related(
                'images'  # Prefetch all related images without using a custom attribute
            )  # Optimize OneToOne relations
            # .prefetch_related(
            #     Prefetch('images', queryset=Image.objects.all(), to_attr='prefetched_images')
            # )
        )

        # Ensure that 'orderitem' prefetches not only 'product' but also detailed relationships
        order_items_prefetch = Prefetch(
            'orderitem',
            queryset=OrderItem.objects.all().prefetch_related(product_prefetch)
        )

        return (
            Order.objects.filter(user=user.profile)
            .prefetch_related(order_items_prefetch, 'orderitem__product')
            .prefetch_related('products')
            .order_by("-created_at")  # Most recent orders first
        )


@extend_schema(tags=["Merchant"])
class OrderRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user.profile).order_by("-pk")

    def destroy(self, request, *args, **kwargs):
        """IMPORTANT:
        Front ba'zan savatdan bitta mahsulotni o'chirish uchun shu endpointga (order delete)
        OrderItem `id` yuborib yuboradi. Default behavior esa Order'ni o'chiradi va CASCADE
        orqali savatdagi hamma itemlar ketib qoladi.

        Shu sababli, avval `pk` ni cartdagi OrderItem sifatida tekshiramiz.
        Topilsa — faqat bitta item o'chiriladi. Aks holda, order delete faqat savatdan
        tashqaridagi (in_cart emas) orderlar uchun ishlaydi.
        """

        pk = kwargs.get("pk")
        user_profile = request.user.profile

        # 1) Agar pk userning orderiga tegishli bo'lsa va u savat (in_cart) bo'lmasa,
        #    bu haqiqiy order delete bo'lib qoladi.
        maybe_order = Order.objects.filter(pk=pk, user=user_profile).first()
        if maybe_order is not None and maybe_order.status != "in_cart":
            return super().destroy(request, *args, **kwargs)

        # 2) Aks holda (ko'pincha front savat item id yuboradi), pk ni OrderItem deb ko'ramiz.
        cart_item = (
            OrderItem.objects.filter(
                pk=pk,
                order__user=user_profile,
                order__status="in_cart",
            )
            .select_related("order")
            .first()
        )
        if cart_item is not None:
            order = cart_item.order
            cart_item.delete()
            order.update_total_amount()

            success_message = {
                "uz": "Maxsulot savatdan o'chirib tashlandi",
                "ru": "Товар удален из корзины",
                "en": "The product has been removed from the cart",
                "kr": _("제품이 장바구니에서 제거되었습니다"),
            }
            return Response({"message": success_message}, status=status.HTTP_204_NO_CONTENT)

        # 3) pk savat order bo'lsa — orderni o'chirmaymiz (aks holda hamma itemlar ketadi).
        if maybe_order is not None and maybe_order.status == "in_cart":
            return Response(
                {
                    "detail": "Savatni (order) o'chirish mumkin emas. Bitta mahsulotni o'chirish uchun order-item endpointidan foydalaning."  # noqa: E501
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4) Hech narsa topilmadi
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["Merchant"])
class OrderItemCreateAPIView(CreateAPIView):
    queryset = OrderItem.objects.all().order_by("-pk")
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """
        Bu metod serializerga qo'shimcha kontekstni o'tkazish uchun ishlatiladi.
        """
        context = super(OrderItemCreateAPIView, self).get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Multi-language success message for product addition
        success_message = {
            "en": _("The product has been successfully added to the cart"),
            "uz": _("Maxsulot savatga muvafaqqiyatli qo'shildi"),
            "ru": _("Товар успешно добавлен в корзину"),
            "kr": _("제품이 장바구니에 성공적으로 추가되었습니다"),
        }

        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": success_message, "order_item": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema(tags=["Merchant"])
class OrderItemListAPIView(ListAPIView):
    queryset = OrderItem.objects.all().order_by("-pk")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination


@extend_schema(tags=["Merchant"])
class OrderItemRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Login qilgan userni aniqlaymiz
        user_profile = self.request.user.profile
        # Faqat shu userga tegishli bo'lgan "savatdagi" narsalarni qaytaramiz
        return OrderItem.objects.filter(order__user=user_profile)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        order = instance.order
        self.perform_destroy(instance)
        order.update_total_amount()

        success_message = {
            "uz": "Maxsulot savatdan o'chirib tashlandi",
            "ru": "Товар удален из корзины",
            "en": "The product has been removed from the cart",
            "kr": _("제품이 장바구니에서 제거되었습니다"),
        }
        return Response({"message": success_message}, status=status.HTTP_204_NO_CONTENT)

@extend_schema(tags=["Merchant"])
class InformationListAPIView(ListAPIView):
    queryset = Information.objects.all().order_by("-pk")
    serializer_class = InformationSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination


@extend_schema(tags=["Merchant"])
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id, *args, **kwargs):
        with transaction.atomic():
            try:

                # Check the original Order
                original_order = Order.objects.get(
                    id=order_id, user=request.user.profile
                )

                if original_order.status in ["approved", "sent", "cancelled"]:
                    new_order = Order.objects.create(
                        user=request.user.profile, status="pending"
                    )
                    for item in original_order.orderitem_set.all():
                        OrderItem.objects.create(
                            order=new_order,
                            product=item.product,
                            quantity=item.quantity,
                        )
                    order = new_order
                else:
                    order = original_order

                update_data = request.data.copy()
                update_data["status"] = "pending"
                serializer = OrderStatusUpdateSerializer(order, data=update_data)
                if serializer.is_valid():
                    serializer.save()
                    # Logic for sending message to a bot
                    bot(order)

                    # Multi-language success message for order creation
                    success_message = {
                        "en": _("Order created successfully"),
                        "uz": _("Buyurtma muvafaqqiyatli yaratildi"),
                        "ru": _("Заказ успешно создан"),
                        "kr": _("주문이 성공적으로 생성되었습니다"),
                    }

                    return Response(
                        {
                            "status": "success",
                            "order_id": order.id,
                            "message": success_message,
                        }
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Order.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Order not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )


@extend_schema(tags=["Merchant"])
class ServiceListAPIView(ListAPIView):
    queryset = Service.objects.all().order_by("-pk")
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination


@extend_schema(tags=["Merchant"])
class SocialMeadiaAPIView(ListAPIView):
    queryset = SocialMedia.objects.all().order_by("-pk")
    serializer_class = SocialMediaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination


@extend_schema(tags=["Merchant"])
class BonusPIView(ListAPIView):
    queryset = Bonus.objects.all().order_by("pk")
    serializer_class = BonusSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination


@extend_schema(tags=["LoyaltyCard"])
class MyLoyaltyCardAPIView(APIView):
    # Только залогиненный пользователь может получить данные
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Возвращает карту лояльности ТОГО пользователя, который сделал запрос
        """
        try:
            # 1. Получаем профиль текущего пользователя через токен
            user_profile = request.user.profile

            # 2. Ищем карту, которая принадлежит этому профилю
            card = LoyaltyCard.objects.get(profile=user_profile)

            # 3. Отдаем данные в сериализатор
            serializer = LoyaltyCardSerializer(card)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except AttributeError:
            # Если у юзера вдруг нет профиля
            return Response({"error": "Profile not found"}, status=status.HTTP_400_BAD_REQUEST)
        except LoyaltyCard.DoesNotExist:
            # Если карта еще не создана
            return Response({"detail": "Loyalty card not found for this user"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["Bonus kismi referal History"])
class MyBonusScreenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 🔥 ENG MUHIM JOY
        profile = request.user.profile

        serializer = UserBonusSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(tags=["Savat Otkazish"])
class CartManageAPIView(APIView):
    serializer_class = CartAddSerializer

    @swagger_auto_schema(request_body=CartAddSerializer)
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order, _ = Order.objects.get_or_create(user=request.user.profile, status='in_cart')
        product_id = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        if quantity > 0:
            OrderItem.objects.update_or_create(order=order, product_id=product_id, defaults={'quantity': quantity})
        else:
            OrderItem.objects.filter(order=order, product_id=product_id).delete()

        order.update_total_amount()
        return Response({"message": "Savat yangilandi", "total": order.total_amount})


@extend_schema(tags=["Zakaz Oformit kilish"])
class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    @swagger_auto_schema(request_body=CheckoutSerializer)
    def post(self, request):
        user_profile = request.user.profile
        # Savatdagi buyurtmani topamiz
        order = Order.objects.filter(user=user_profile, status='in_cart').first()

        if not order or not order.orderitem.exists():
            return Response({"error": "Savat bo'sh"}, status=400)

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1. Location obyektini serializerdan olamiz
        location_obj = serializer.validated_data['location']

        # 2. Buyurtmaga biriktiramiz va saqlaymiz
        order.location = location_obj
        order.comment = serializer.validated_data.get('comment', '')
        order.status = 'payment_pending'
        order.save()

        # 3. Javob qaytaramiz (manzil matni bilan birga)
        return Response({
            "message": "Buyurtmangiz adminga yuborildi. Tasdiqlangach to'lov qilishingiz mumkin.",
            "order_id": order.id,
            "status": "payment_pending",
            "delivery_address": order.location.address,  # <--- MANA SHU YERDA MANZIL CHIQADI
            "total_amount": order.total_amount
        })


# --- 3. CHEK YUKLASH ---
@extend_schema(tags=["Tolov kilish"])
class UploadReceiptAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="To'lov uchun karta ma'lumotlarini olish",
        description="Buyurtma ID-sini yuboring va to'lov qilinishi kerak bo'lgan bank karta ma'lumotlarini oling.",
        parameters=[
            OpenApiParameter("order_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Order ID raqami", required=True),
        ],
        tags=["Tolov kilish"]
    )
    def get(self, request):
        """Foydalanuvchiga to'lov qilish uchun kartani ko'rsatadi"""
        user_profile = request.user.profile
        ord_id = request.query_params.get('order_id')

        if not ord_id:
            return Response({"error": "order_id yuborilishi shart"}, status=400)

        # Buyurtmani topamiz (ID yoki Order Number bo'yicha)
        order = Order.objects.filter(user=user_profile, id=ord_id).first()
        # Agar ID raqam string kelsa, uni int qilib ham tekshirib ko'ramiz
        if not order and str(ord_id).isdigit():
            order = Order.objects.filter(user=user_profile, id=int(ord_id)).first()

        if not order:
            return Response({"error": "Buyurtma topilmadi"}, status=404)

        # --- LOGIKANI O'ZGARTIRDIK ---

        # 1. Avval buyurtmaning o'ziga karta biriktirilganmi qaraymiz
        card = order.bankcard

        # 2. Agar admin biriktirmagan bo'lsa, bazadagi "Default" (birinchi) kartani olamiz
        if not card:
            card = BankCardModel.objects.first()

        # 3. Agar bazada umuman karta bo'lmasa (Admin hali karta yaratmagan bo'lsa)
        if not card:
            return Response({
                "error": "Tizimda to'lov uchun karta mavjud emas. Admin bilan bog'laning."
            }, status=404)

        # 4. Javob qaytaramiz (order.bankcard emas, topilgan 'card' o'zgaruvchisini ishlatamiz)
        return Response({
            "order_id": order.id,
            "order_number": order.order_number,
            "total_amount": order.total_amount,
            "bank_card_number": card.title,  # Karta raqami
            "bank_card_holder": card.card_holder,  # Karta egasi
            "loyalty_balance": user_profile.loyalty_card.current_balance if hasattr(user_profile, 'loyalty_card') else 0
        }, status=200)


    @extend_schema(
        summary="To'lov cheki va Loyalty orqali to'lash (ID bo'yicha)",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'order_id': {'type': 'integer', 'description': 'Buyurtmaning bazadagi ID raqami'},
                    'payment_receipt': {'type': 'string', 'format': 'binary', 'description': 'Chek rasmi'},
                    'loyalty_payment': {'type': 'integer', 'description': 'Loyaltydan yechiladigan summa'}
                },
                'required': ['order_id', 'payment_receipt']
            }
        }
    )
    def post(self, request):
        user_profile = request.user.profile
        ord_id = request.data.get('order_id')  # Flutterchi yuborgan ID
        receipt_file = request.FILES.get('payment_receipt')
        # User yuborgan loyalty summa (agar yubormasa 0 bo'ladi)
        try:
            loyalty_amt = int(request.data.get('loyalty_payment', 0))
        except ValueError:
            return Response({"error": "Loyalty summa raqam bo'lishi shart"}, status=400)

        # 1. Buyurtmani bazadagi 'id' orqali qidiramiz
        order = Order.objects.filter(
            user=user_profile,
            id=ord_id  # <--- Aynan ID bo'yicha qidiruv
        ).exclude(status__in=['approved', 'sent', 'cancelled']).first()

        if not order:
            return Response({"error": "Buyurtma topilmadi yoki to'lov uchun yopiq"}, status=404)

        # 2. Xavfsiz tranzaksiya ochamiz (Pul va Rasm birga ishlashi uchun)
        with transaction.atomic():
            if loyalty_amt > 0:
                # Userda loyalty karta borligini tekshiramiz
                if hasattr(user_profile, 'loyalty_card'):
                    card = user_profile.loyalty_card

                    # Balansni tekshiramiz
                    if card.current_balance >= loyalty_amt:
                        # Balansdan ayiramiz
                        card.current_balance = F('current_balance') - loyalty_amt
                        card.save()

                        # Buyurtmaning o'ziga ham qancha yechilganini yozib qo'yamiz (history uchun)
                        order.loyalty_payment = loyalty_amt
                    else:
                        return Response({"error": "Loyalty kartada mablag' yetarli emas"}, status=400)
                else:
                    return Response({"error": "Sizda loyalty karta mavjud emas"}, status=400)

            # 3. Rasmni saqlaymiz va statusni yangilaymiz
            order.payment_receipt = receipt_file
            order.status = 'pending'  # Avtomatik tasdiqlash
            order.save()

        # Yangilangan balansni olish uchun kartani qayta yuklaymiz
        user_profile.loyalty_card.refresh_from_db()

        return Response({
            "message": "To'lov muvaffaqiyatli! Rasm yuklandi va loyaltydan pul yechildi.",
            "order_id": order.id,
            "order_status": order.status,
            "new_loyalty_balance": user_profile.loyalty_card.current_balance
        }, status=200)


# 2. Bitta buyurtmaning batafsil ma'lumoti (Detail)
@extend_schema(tags=["Bitta buyurtmaning batafsil ma'lumoti"])
class MyOrderDetailView(RetrieveAPIView):  # APIView o'rniga RetrieveAPIView qulayroq
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Bu yerda ham xavfsizlik uchun faqat userning o'ziga tegishli orderlarni filtrlaymiz
        # Shunda birovning ID sini yozsa ham 404 (Topilmadi) beradi
        return Order.objects.filter(user=self.request.user.profile)


@extend_schema(tags=["Buyurtmalar ro'yxati"])
class MyOrdersListView(ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        # Faqat login qilgan userning savatda bo'lmagan buyurtmalarini chiqaradi
        return Order.objects.filter(
            user=self.request.user.profile
        ).exclude(status='in_cart').order_by('-pk')
        # Savatda bo'lmagan, ya'ni haqiqiy buyurtma bo'lgan narsalar
        return Order.objects.filter(user=self.request.user.profile).exclude(status='in_cart').order_by('-pk')


@extend_schema(tags=["LoyaltyHistory"])
class LoyaltyHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.profile

        # 1. Chiqimlar: loyalty_payment 0 dan katta bo'lgan buyurtmalar
        spending = Order.objects.filter(
            user=user_profile,
            loyalty_payment__gt=0
        ).order_by('-created_at')

        # 2. Kirimlar (Cashback): Shaxsiy buyurtma bonuslari
        cashback = LoyaltyPendingBonus.objects.filter(
            profile=user_profile
        ).order_by('-created_at')

        # 3. Kirimlar (Referral): Taklif qilingan do'stlar
        referrals = Referral.objects.filter(
            referrer=user_profile
        ).order_by('-created_at')

        # 4. Hozirgi balansni olish
        balance = 0
        if hasattr(user_profile, 'loyalty_card'):
            balance = user_profile.loyalty_card.current_balance

        # Ma'lumotlarni serializerlarga beramiz
        data = {
            "current_balance": balance,
            "spending_history": LoyaltySpendingHistorySerializer(spending, many=True).data,
            "cashback_history": LoyaltyEarnedHistorySerializer(cashback, many=True).data,
            "referral_history": ReferralHistorySerializer(referrals, many=True).data
        }

        return Response(data)

@extend_schema(tags=["Savatdagi mahsulot sonini yangilash"])
class UpdateCartQuantityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="(Product ID orqali)",
        request=CartUpdateQuantitySerializer,
        responses={200: {"message": "Savat yangilandi", "total_amount": 15000}},
        tags=["Savatdagi mahsulot sonini yangilash"]
    )
    def post(self, request):
        serializer = CartUpdateQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_profile = request.user.profile
        order_id = serializer.validated_data['order_id']
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        # 1. Aynan shu ID ga tegishli va aynan shu userga tegishli buyurtmani topamiz
        # Xavfsizlik uchun faqat 'in_cart' statusidagilarni o'zgartirishga ruxsat beramiz
        order = Order.objects.filter(
            id=order_id,
            user=user_profile,
            status='in_cart'
        ).first()

        if not order:
            return Response(
                {"error": "Bunday buyurtma topilmadi yoki u allaqachon tasdiqlangan."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Savat ichidan o'sha mahsulotni (OrderItem) qidiramiz
        order_item = OrderItem.objects.filter(order=order, product_id=product_id).first()

        if not order_item:
            return Response({"error": "Bu mahsulot ushbu savatda mavjud emas"}, status=404)

        # 3. Miqdorni yangilaymiz yoki o'chiramiz
        if quantity > 0:
            order_item.quantity = quantity
            order_item.save()
            message = "Miqdor yangilandi"
        else:
            order_item.delete()
            message = "Mahsulot o'chirildi"

        # 4. Jami summani qayta hisoblaymiz
        order.update_total_amount()

        return Response({
            "message": message,
            "total_amount": order.total_amount,
            "order_id": order.id
        }, status=status.HTTP_200_OK)


