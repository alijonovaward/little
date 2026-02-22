from django.urls import path
from .views import (
    # Categories
    CategoryListAPIView,

    # Tickets
    TicketListAPIView,
    NewTicketsListView,
    PopularTicketsAPIView,
    TicketsOnSaleListView,
    TicketVariantsAPIView,

    # Phones
    PhoneListAPIView,
    NewPhonesListView,
    PopularPhonesAPIView,
    PhonesOnSaleListView,
    PhoneVariantsAPIView,

    # Goods
    GoodListAPIView,
    NewGoodsListView,
    PopularGoodAPIView,
    GoodsOnSaleListView,
    GoodVariantsAPIView,

    # General & Search
    ImageListAPIView,
    MultiProductSearchView,
    RegularProductListAPIView,
    WholesaleProductAPIView, GoodDetailAPIView, GoodAllListAPIView,
)

urlpatterns = [
    # Categories (SubCategory o'chirildi)
    path("categories/list/", CategoryListAPIView.as_view(), name='category-list'),

    # Tickets
    path("tickets/list/", TicketListAPIView.as_view(), name='ticket-list'),
    path("new-tickets/list/", NewTicketsListView.as_view(), name='new-tickets'),
    path("popular-tickets/list/", PopularTicketsAPIView.as_view(), name='popular-tickets'),
    path("sale-tickets/list/", TicketsOnSaleListView.as_view(), name='sale-tickets'),
    path('ticket-variants/<uuid:product_type>/', TicketVariantsAPIView.as_view(), name='ticket-variants'),

    # Phones
    path("phones/list/", PhoneListAPIView.as_view(), name='phone-list'),
    path("new-phones/list/", NewPhonesListView.as_view(), name='new-phones'),
    path("popular-phones/list/", PopularPhonesAPIView.as_view(), name='popular-phones'),
    path("sale-phones/list/", PhonesOnSaleListView.as_view(), name='sale-phones'),
    path('phone-variants/<uuid:product_type>/', PhoneVariantsAPIView.as_view(), name='phone-variants'),

    # Goods
    path("goods/list/", GoodListAPIView.as_view(), name='good-list'),
    path("new-goods/list/", NewGoodsListView.as_view(), name='new-goods'),
    path("popular-goods/list/", PopularGoodAPIView.as_view(), name='popular-goods'),
    path("sale-goods/list/", GoodsOnSaleListView.as_view(), name='sale-goods'),
    path('good-variants/<uuid:product_type>/', GoodVariantsAPIView.as_view(), name='good-variants'),

    # Images & Search
    path("images/list/", ImageListAPIView.as_view(), name='image-list'),
    path("product-search/", MultiProductSearchView.as_view(), name='product-search'),

    # Products (B2C & Wholesale)
    path('products/', RegularProductListAPIView.as_view(), name='product-list-all'),

    path('goods/', GoodAllListAPIView.as_view(), name='good-list'),
    path('goods/<int:pk>/', GoodDetailAPIView.as_view(), name='good-detail'),
]
