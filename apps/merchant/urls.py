from django.urls import path

from apps.merchant.views import *

urlpatterns = [
    # Orders
    path("order/create/", OrderCreateAPIView.as_view()),
    path("order/list/", OrderListAPIView.as_view()),
    path("order/<int:pk>/retriev/", OrderRetrieveUpdateDelete.as_view()),

    # Order items
    path("order-item/create/", OrderItemCreateAPIView.as_view()),
    path("order-item/list/", OrderItemListAPIView.as_view()),
    path("order-item/<int:pk>/retriev/", OrderItemRetrieveUpdateDelete.as_view()),

    # Checkout & info
    path("checkout/<int:order_id>/", CheckoutView.as_view(), name="checkout"),
    path("information/", InformationListAPIView.as_view(), name="info"),
    path("service/", ServiceListAPIView.as_view(), name="service"),
    path("social-media-urls/", SocialMeadiaAPIView.as_view()),

    # Bonus
    path("bonus-list/", BonusPIView.as_view()),
    path("my-bonus/", MyBonusScreenAPIView.as_view(), name="my-bonus"),
    path("my-loyalty-card/", MyLoyaltyCardAPIView.as_view(), name="merchant-my-loyalty-card"),

    # 1. Savatni boshqarish (Mahsulot qo'shish, sonini o'zgartirish yoki o'chirish)
    # Flutterchi JSON yuboradi: {"product": 1, "quantity": 2}
    path('cart/manage/', CartManageAPIView.as_view(), name='cart-manage'),

    # 2. Buyurtmani rasmiylashtirish (Savatni yopish va "To'lov kutilmoqda" holatiga o'tkazish)
    # Flutterchi JSON yuboradi: {"location": 5, "comment": "..."}
    path('cart/checkout/', CheckoutAPIView.as_view(), name='cart-checkout'),

    # 3. To'lov chekini (rasm) yuklash
    # URL format: /api/merchant/order/15/upload-receipt/
    path('order/upload-receipt/', UploadReceiptAPIView.as_view(), name='upload-receipt'),

    path('orders/', MyOrdersListView.as_view(), name='my-orders-list'),
    path('orders/<int:pk>/', MyOrderDetailView.as_view(), name='my-order-detail'),

    path('loyalty/history/', LoyaltyHistoryAPIView.as_view(), name='loyalty-history'),

    path('cart/update-quantity/', UpdateCartQuantityAPIView.as_view(), name='update-cart-quantity'),
    path('user/b2b-status/', B2BStatusAPIView.as_view(), name='b2b-status'),
    path('cart/remove-item/', RemoveFromCartAPIView.as_view(), name='remove-from-cart'),
]
