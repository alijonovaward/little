from django.db.models import Q, Exists, OuterRef, F, Sum, Value, BooleanField
from django.conf import settings
import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import views, status, generics
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from apps.customer.models import Favorite
from .models import Category, Good, Image, Phone, Ticket, ProductItem
from .permissions import IsApprovedWholesaler
from .serializers import (
    CategorySerializer, CustomPageNumberPagination, GoodSerializer,
    GoodVariantSerializer, ImageSerializer, PhoneSerializer,
    PhoneVariantSerializer, TicketSerializer, TicketPopularSerializer,
    PhonePopularSerializer, GoodPopularSerializer, TicketVariantSerializer,
    ProductItemSerializer, GoodFullSerializer
)




# --- Base Mixin for Optimization ---

class ProductOptimizationMixin:
    """
    Queryset'larni optimallashtirish va is_favorite maydonini
    annotation orqali qo'shish uchun umumiy klass.
    """
    pagination_class = CustomPageNumberPagination
    def get_optimized_queryset(self, model_class, relation_name=None):
        user = self.request.user
        queryset = model_class.objects.select_related("product").prefetch_related("product__images")

        if user.is_authenticated:
            favorites_subquery = Favorite.objects.filter(
                user=user.profile, product_id=OuterRef("product_id")
            )
            queryset = queryset.annotate(is_favorite=Exists(favorites_subquery))
        else:
            queryset = queryset.annotate(is_favorite=Value(False, output_field=BooleanField()))

        return queryset.order_by("-pk")


# --- Category Views ---

@extend_schema(tags=["Product"])
class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("-pk")
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name", "main_type"]
    filterset_fields = ["main_type"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]


# SubCategoryListAPIView butunlay olib tashlandi.

# --- Product List Views ---

@extend_schema(tags=["Product"])
class TicketListAPIView(ProductOptimizationMixin, generics.ListAPIView):
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["product", "product__product_type", "category"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_optimized_queryset(Ticket)


@extend_schema(tags=["Product"])
class PhoneListAPIView(ProductOptimizationMixin, generics.ListAPIView):
    serializer_class = PhoneSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["category", "product", "product__product_type"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_optimized_queryset(Phone)


class GoodFilter(FilterSet):
    category = django_filters.NumberFilter(field_name="category")
    
    class Meta:
        model = Good
        fields = ["product", "product__product_type"]

@extend_schema(tags=["Product"])
class GoodListAPIView(ProductOptimizationMixin, generics.ListAPIView):
    pagination_class = CustomPageNumberPagination
    serializer_class = GoodSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = GoodFilter
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Faqat main=True bo'lganlarni chiqarish
        return self.get_optimized_queryset(Good).filter(product__main=True)


# --- Variant Views (Optimallashtirildi) ---

class BaseVariantAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    pagination_class = CustomPageNumberPagination

    def get(self, request, product_type):
        items = self.model.objects.filter(product__product_type=product_type).select_related(
            "product").prefetch_related("product__images")
        if not items.exists():
            return Response({"detail": f"No {self.model.__name__} found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(items, many=True, context={"request": request})
        return Response(serializer.data)


class GoodVariantsAPIView(BaseVariantAPIView):
    pagination_class = CustomPageNumberPagination
    model = Good
    serializer_class = GoodVariantSerializer


class TicketVariantsAPIView(BaseVariantAPIView):
    pagination_class = CustomPageNumberPagination
    model = Ticket
    serializer_class = TicketVariantSerializer


class PhoneVariantsAPIView(BaseVariantAPIView):
    pagination_class = CustomPageNumberPagination
    model = Phone
    serializer_class = PhoneVariantSerializer


# --- Popular Products ---

@extend_schema(tags=["Product"])
class PopularTicketsAPIView(generics.ListAPIView):
    serializer_class = TicketPopularSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return Ticket.objects.select_related("product").annotate(
            sold_count=Sum("product__sold_products__quantity")
        ).order_by("-sold_count")


@extend_schema(tags=["Product"])
class PopularPhonesAPIView(generics.ListAPIView):
    pagination_class = CustomPageNumberPagination
    serializer_class = PhonePopularSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Phone.objects.select_related("product").annotate(
            sold_count=Sum("product__sold_products__quantity")
        ).order_by("-sold_count")


@extend_schema(tags=["Product"])
class PopularGoodAPIView(ProductOptimizationMixin, generics.ListAPIView):
    pagination_class = CustomPageNumberPagination
    serializer_class = GoodPopularSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_optimized_queryset(Good).annotate(
            sold_count=Sum("product__sold_products__quantity")
        ).order_by("-sold_count")


# --- Sale (Chegirma) Views ---

class BaseSaleListView(ProductOptimizationMixin, generics.ListAPIView):
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]
    model = None

    def get_queryset(self):
        return self.get_optimized_queryset(self.model).filter(
            product__new_price__lt=F("product__old_price")
        )


class TicketsOnSaleListView(BaseSaleListView):
    model = Ticket
    serializer_class = TicketSerializer
    pagination_class = CustomPageNumberPagination

class PhonesOnSaleListView(BaseSaleListView):
    model = Phone
    serializer_class = PhoneSerializer
    pagination_class = CustomPageNumberPagination

class GoodsOnSaleListView(BaseSaleListView):
    model = Good
    serializer_class = GoodSerializer
    pagination_class = CustomPageNumberPagination

# --- Search ---

@extend_schema(tags=["Product"])
class MultiProductSearchView(views.APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    def get(self, request):
        search_query = request.query_params.get("search", None)
        if not search_query:
            return Response({"message": "No search query provided"}, status=400)

        def build_query(field_name):
            query = Q()
            for lang in settings.MODELTRANSLATION_LANGUAGES:
                query |= Q(**{f"{field_name}_{lang}__icontains": search_query})
            return query

        context = {"request": request}
        results = {
            "tickets": TicketSerializer(Ticket.objects.filter(build_query("event_name")), many=True,
                                        context=context).data,
            "phones": PhoneSerializer(Phone.objects.filter(build_query("model_name")), many=True, context=context).data,
            "goods": GoodSerializer(Good.objects.filter(build_query("name")), many=True, context=context).data,
        }
        return Response(results)


# --- Other Views ---

@extend_schema(tags=["Product"])
class ImageListAPIView(generics.ListAPIView):
    queryset = Image.objects.all().order_by("-pk")
    serializer_class = ImageSerializer
    filterset_fields = ["product"]
    permission_classes = [IsAuthenticated]


@extend_schema(tags=["Product"])
class WholesaleProductAPIView(views.APIView):
    permission_classes = [IsApprovedWholesaler]

    def get(self, request):
        products = ProductItem.objects.filter(active=True, wholesale_price__gt=0)
        serializer = ProductItemSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


# views.py ichiga qo'shib qo'ying (agar bo'lmasa)
class NewTicketsListView(BaseSaleListView):  # Yoki ProductOptimizationMixin dan foydalaning
    model = Ticket
    serializer_class = TicketSerializer
    pagination_class = CustomPageNumberPagination
    def get_queryset(self):
        return self.get_optimized_queryset(Ticket).order_by("-product__created")


class NewPhonesListView(NewTicketsListView):
    model = Phone
    serializer_class = PhoneSerializer
    pagination_class = CustomPageNumberPagination

class NewGoodsListView(NewTicketsListView):
    model = Good
    serializer_class = GoodSerializer
    pagination_class = CustomPageNumberPagination

@extend_schema(tags=["Product"])
class RegularProductListAPIView(ListAPIView):


    queryset = ProductItem.objects.filter(active=True)
    serializer_class = ProductItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    # Generic ichidagi funksiyani override qilish
    def get_queryset(self):
        # Bu yerda qo'shimcha filtrlar yozish mumkin
        queryset = super().get_queryset()
        # Masalan, qidiruv (search) kiritish mumkin:
        q = self.request.query_params.get('search')
        if q:
            queryset = queryset.filter(desc__icontains=q)
        return queryset


    # Serializerga context yuborishni ta'minlash
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

@extend_schema(tags=["Main_Product"])
class GoodAllListAPIView(generics.ListAPIView):
    """
    Barcha oziq-ovqatlar ro'yxati (Faqat main=True bo'lganlar)
    """
    serializer_class = GoodFullSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = GoodFilter
    search_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        # Ro'yxatda faqat ASOSIY mahsulotlarni chiqaramiz
        # queryset = Good.objects.filter(
        #     product__main=True,
        #     product__active=True
        # ).select_related('product').prefetch_related('product__images')
        queryset = Good.objects.all()

        # Is_favorite tekshiruvi
        # if user.is_authenticated:
        #     favs = Favorite.objects.filter(user=user.profile, product_id=OuterRef('product_id'))
        #     queryset = queryset.annotate(is_favorite=Exists(favs))

        return queryset

@extend_schema(tags=["Product_Related"])
class GoodDetailAPIView(generics.RetrieveAPIView):
    """
    Bitta mahsulot tafsiloti (Hamma tillar va variantlar bilan)
    """
    queryset = Good.objects.all().select_related('product')
    serializer_class = GoodFullSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated:
            favs = Favorite.objects.filter(user=user.profile, product_id=OuterRef('product_id'))
            queryset = queryset.annotate(is_favorite=Exists(favs))
        return queryset
