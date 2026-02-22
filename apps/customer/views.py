import random
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from .base import CustomerFilterService, CustomerListService
from .models import (
    B2BApplication,
    Banner,
    Favorite,
    Location,
    News,
    Profile,
    ViewedNews,
)
from .serializers import (
    B2BApplicationCreateSerializer,
    BannerSerializer,
    CustomPageNumberPagination,
    FavoriteListSerializer,
    FavoriteSerializer,
    LocationListSerializer,
    LocationSerializer,
    LoginSerializer,
    NewsSerializer,
    ProfileSerializer,
    RegisterSerializer,
    SetPasswordSerializer,
    VerifyOTPSerializer,
    ViewedNewsSerializer,
)
from .utils import generate_otp
from ..merchant.models import Referral

User = get_user_model()


@extend_schema(tags=["Authentication"])
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        tags=["Authentication"],
        operation_summary="Вход в систему",
        request_body=LoginSerializer,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            profile = user.profile

            # 1. Flutterdan kelgan tokenni olamiz
            device_token = serializer.validated_data.get('device_token')

            # 2. Agar token kelgan bo'lsa, uni profilga saqlaymiz
            if device_token:
                profile.device_token = device_token
                profile.save()

            refresh = RefreshToken.for_user(user)

            # B2B Status
            is_b2b = getattr(user, "is_b2b", False)
            
            # Application Status
            application_status = None
            last_app = B2BApplication.objects.filter(user=user).order_by("-created").first()
            if last_app:
                application_status = last_app.status

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'full_name': profile.full_name,
                'is_b2b': is_b2b,
                'application_status': application_status,
                'message': "Muvaffaqiyatli kirdingiz"
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Customer"])
class ProfileCreateAPIView(CreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
class ProfileUpdate(APIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        user = self.request.user
        try:
            profile = user.profile

        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=["Customer"])
class ProfileDelete(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.delete()
        return Response(
            {"message": "User has been successfully deleted"},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Customer"])
class LocationCreateAPIView(CreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)


@extend_schema(tags=["Customer"])
class LocationListAPIView(ListAPIView):
    """
    Barcha location'larni list qilish
    Filter va search bilan
    """
    serializer_class = LocationListSerializer
    filter_backends = CustomerFilterService.get_filter_backends()
    search_fields = CustomerFilterService.get_location_search_fields()
    filterset_fields = ["user__full_name", "address"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        # ВАЖНО: Фильтруем данные, чтобы юзер видел только свои локации
        return Location.objects.filter(user=self.request.user.profile).order_by("-pk")


@extend_schema(tags=["Customer"])
class LocationRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


@extend_schema(tags=["Customer"])
class NewsListAPIView(ListAPIView):
    """
    Barcha yangiliklarni list qilish
    Filter va search bilan
    """
    serializer_class = NewsSerializer
    filter_backends = CustomerFilterService.get_filter_backends()
    search_fields = CustomerFilterService.get_news_search_fields()
    filterset_fields = ["description"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return CustomerListService.get_news_list()


@extend_schema(tags=["Customer"])
class NewsRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer


@extend_schema(tags=["Customer"])
class ViewedNewsCreateAPIView(CreateAPIView):
    queryset = ViewedNews.objects.all()
    serializer_class = ViewedNewsSerializer


@extend_schema(tags=["Customer"])
class FavoriteCreateAPIView(CreateAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)

    def create(self, request, *args, **kwargs):
        # Front product yuborishda 2 xil format bo'lishi mumkin:
        # 1) {"product": <id>}  (DRF standart)
        # 2) {"product_id": <id>} (talab bo'yicha)
        data = request.data.copy()
        if "product" not in data and "product_id" in data:
            data["product"] = data.get("product_id")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except IntegrityError:
            return Response(
                {"message": "This favorite item already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Customer"])
class RemoveFromFavoritesView(APIView):
    # /api/customer/remove_from_favorites/<product_id>/ -> UNLIKE (product_id bo'yicha)
    permission_classes = [IsAuthenticated]

    def _delete_by_product_id(self, request, product_id):
        # Like ID bilan emas, aynan product_id bo'yicha o'chiramiz:
        # login bo'lgan user + product_id
        try:
            favorite = Favorite.objects.get(user=request.user.profile, product_id=product_id)
            favorite.delete()
            return Response({"status": "success"}, status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response(
                {"error": "Item not found in favorites"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, product_id, *args, **kwargs):
        return self._delete_by_product_id(request, product_id)

    # Front o'zgarmasin: eski loyihada POST ishlatilgan bo'lishi mumkin.
    # Shu bilan birga, DELETE (unlike) ham ishlayversin.
    def delete(self, request, product_id, *args, **kwargs):
        return self._delete_by_product_id(request, product_id)


@extend_schema(tags=["Customer"])
class FavoriteListAPIView(ListAPIView):
    """
    Foydalanuvchining sevimli mahsulotlarini list qilish
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = FavoriteListSerializer
    filter_backends = CustomerFilterService.get_filter_backends()
    search_fields = CustomerFilterService.get_favorite_search_fields()
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Favorite.objects.none()

        # Faqat login bo'lgan user'ning sevimlilari (leak bo'lmasin)
        return (
            Favorite.objects.filter(user=self.request.user.profile)
            .order_by("-pk")
            .select_related(
                'product__tickets',
                'product__goods',
                'product__phones'
            )
            .prefetch_related('product__images')
        )


@extend_schema(tags=["Customer"])
class FavoriteRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

    # /api/customer/favorite/<pk>/retrieve/ -> front ba'zan pk=product_id yuboradi.
    # Shart: delete (unlike) LIKE ID bilan emas, product_id bilan ishlasin.
    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        # 1) Avval pk ni product_id deb ko'ramiz (talab bo'yicha)
        favorite = Favorite.objects.filter(user=request.user.profile, product_id=pk).first()
        if favorite is None:
            # 2) Fallback: agar front eskicha favorite id yuborsa ham, faqat o'ziga tegishlisini o'chirsin
            favorite = Favorite.objects.filter(user=request.user.profile, pk=pk).first()

        if favorite is None:
            return Response({"error": "Item not found in favorites"}, status=status.HTTP_404_NOT_FOUND)

        favorite.delete()
        return Response({"status": "success"}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Authentication"])
class RegisterView(APIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    authentication_classes = []

    @swagger_auto_schema(
        operation_summary="Регистрация и вход по OTP",
        operation_description="Отправляет OTP на телефон. Если пользователь новый и указан реферал-код, пригласившему сразу начисляется 5000 вон.",
        request_body=RegisterSerializer,
        responses={
            200: openapi.Response(
                description="Успешная отправка СМС",
                examples={
                    "application/json": {
                        "message": "OTP code sent to your phone",
                        "referral_code": "ABC12345",
                        "otp_debug": "5566"
                    }
                }
            ),
            400: "Неверные данные (валидация)",
            408: "Ошибка отправки СМС (Twilio)"
        },
        tags=['Authentication']  # Группировка в Swagger
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        full_name = serializer.validated_data.get("full_name", "")
        referral_code = serializer.validated_data.get("referral_code")

        otp_code = str(random.randint(1000, 9999))

        try:
            with transaction.atomic():
                # Создаем/получаем юзера
                user, _ = User.objects.get_or_create(username=phone_number)

                # Создаем/обновляем профиль
                profile, profile_created = Profile.objects.get_or_create(
                    origin=user,
                    defaults={
                        "full_name": full_name,
                        "phone_number": phone_number,
                        "otp": otp_code
                    }
                )

                if not profile_created:
                    profile.otp = otp_code
                    profile.save()

                # Логика реферала (Мгновенный бонус)
                if profile_created and referral_code:
                    try:
                        referrer = Profile.objects.get(referral_code=referral_code)
                        if referrer != profile:
                            # Ставим статус 'rewarded' для автоматического начисления
                            Referral.objects.create(
                                referrer=referrer,
                                referee=profile,
                                status='rewarded'
                            )
                    except Profile.DoesNotExist:
                        pass  # Код неверный - игнорируем

            # Отправка СМС
            send_otp_sms(phone_number, otp_code)

            return Response({
                "message": "OTP code sent to your phone",
                "referral_code": profile.referral_code,
                "otp_debug": otp_code
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "Internal server error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Authentication"])
class VerifyRegisterOTPView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        profile = Profile.objects.get(phone_number=phone_number)
        profile.otp = None
        profile.save()

        # Multi-language success message for account activation
        success_message = {
            "en": _("Account activated successfully"),
            "uz": _("Akkount muvafaqqiyatli faollashtirildi"),
            "ru": _("Аккаунт успешно активирован"),
            "kr": _("계정이 성공적으로 활성화되었습니다"),
        }

        return Response(
            {"message": success_message},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Authentication"])
class SetPasswordView(APIView):
    serializer_class = SetPasswordSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Authentication"],
        request_body=SetPasswordSerializer,
        responses={
            200: "Password set successfully",
            400: "Bad request"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(username=phone_number)
            user.set_password(new_password)
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "token": token.key,
                    "message": "Password set successfully"
                },
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(tags=["Customer"])
class BannerListAPIView(ListAPIView):
    """
    Barcha banner'larni list qilish
    """
    serializer_class = BannerSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return CustomerListService.get_banners_list()


@extend_schema(tags=["Customer"])
class ProfileEditAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Foydalanuvchining profili olindi, agar yo'q bo'lsa, 404 xato qaytariladi
        profile = Profile.objects.get(origin=self.request.user)
        return profile


@extend_schema(tags=["Customer"])
class LatestUnviewedNewsView(APIView):
    def get(self, request, *args, **kwargs):
        latest_news = News.get_latest_unviewed_news(request.user.profile)
        if latest_news:
            serializer = NewsSerializer(latest_news)
            return Response(serializer.data)
        return Response(
            {"message": "Barcha yangiliklar ko'rilgan"},
            status=status.HTTP_404_NOT_FOUND,
        )


@extend_schema(tags=["Customer"])
class MarkNewsAsViewed(APIView):
    serializer_class = ViewedNewsSerializer

    def post(self, request, *args, **kwargs):
        serializer = ViewedNewsSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Yangilik o'qildi sifatida belgilandi"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# /api/customer/b2b/apply/ -> B2B ariza yuborish (frontenddagi "Ariza yuborish")
@extend_schema(
    tags=["B2B"],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'company_name': {'type': 'string'},
                'phone': {'type': 'string'},
                'address': {'type': 'string'},
                'contact_person': {'type': 'string'},
                'extra_info': {'type': 'string'},
                'document_image': {
                    'type': 'string',
                    'format': 'binary'
                }
            },
            'required': ['company_name', 'phone', 'address', 'contact_person']
        }
    },
    responses={201: B2BApplicationCreateSerializer}
)
class B2BApplicationCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = B2BApplicationCreateSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        if B2BApplication.objects.filter(
            user=self.request.user,
            status=B2BApplication.Status.PENDING,
        ).exists():
            raise ValidationError({"detail": "You already have a pending B2B application."})

        serializer.save(user=self.request.user)


# ===== SMS UTILITIES =====

def send_otp_sms(phone_number, otp):
    try:
        sid = settings.TWILIO_ACCOUNT_SID.strip()
        token = settings.TWILIO_AUTH_TOKEN.strip()
        from_number = settings.TWILIO_PHONE_NUMBER.strip()

        client = Client(sid, token)
        message = client.messages.create(
            body=f"Million Mart: Tasdiqlash kodi: {otp}",
            from_=from_number,
            to=phone_number
        )
        print(f"OK! SMS ID: {message.sid}")
    except Exception as e:
        print(f"XATO JONI: {e}")