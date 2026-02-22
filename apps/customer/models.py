import random, string

from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.db import models
from django.db.models import Q
from model_utils.models import TimeStampedModel


# Create your models here.

def generate_referral_code(length=8):
    """Генерирует уникальный код из букв и цифр"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class User(AbstractUser):
    img = models.ImageField(
        upload_to='wholesaler',
        null=True,
        blank=True,
        verbose_name="Rasm"
    )
    is_wholesaler = models.BooleanField(default=False)  # Optomchi xaridor
    is_approved = models.BooleanField(default=False)  # Admin tasdig'i
    is_b2b = models.BooleanField(default=False)  # B2B (kompaniya) mijoz

    def __str__(self):
        return self.username


def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Profile(models.Model):  # Удали TimeStampedModel если она вызывает ошибки, или оставь если она есть
    LANG = (("uz", "UZ"), ("ru", "RU"), ("en", "EN"), ("kr", "KR"))
    origin = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=17)
    lang = models.CharField(max_length=2, choices=LANG, default="uz")
    cashback = models.IntegerField(default=0)
    otp = models.CharField(max_length=100, null=True, blank=True)
    referral_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    device_token = models.TextField(null=True, blank=True)  # Yangi maydon
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            while True:
                code = generate_referral_code()
                if not Profile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    # ВАЖНО: def __str__ должен быть ВНУТРИ класса (с отступом)
    def __str__(self) -> str:
        return f"{self.full_name} ({self.origin.username})"


class B2BApplication(TimeStampedModel, models.Model):
    """B2B ariza modeli.

    /api/customer/b2b/apply/ endpointi shu modelga yozadi.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="b2b_applications",
    )
    company_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    address = models.CharField(max_length=510)
    contact_person = models.CharField(max_length=255)
    extra_info = models.TextField(blank=True)
    document_image = models.ImageField(upload_to="b2b/documents/", null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Admin arizani approved qilsa -> user.is_b2b = True
        if self.status == self.Status.APPROVED and not getattr(self.user, "is_b2b", False):
            self.user.is_b2b = True
            self.user.save(update_fields=["is_b2b"])

    class Meta:
        # 1 user -> 1 ta pending ariza (dublikat bo'lmasin)
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="pending"),
                name="unique_pending_b2b_application_per_user",
            )
        ]


class Location(TimeStampedModel, models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="location")
    address = models.CharField(max_length=510)
    active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.active:
            Location.objects.filter(user=self.user).exclude(id=self.id).update(
                active=False
            )

        super(Location, self).save(*args, **kwargs)


class News(TimeStampedModel, models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="media/news")
    active = models.BooleanField(default=True)

    @classmethod
    def get_latest_unviewed_news(cls, user):
        # Foydalanuvchining ko'rmagan yangiliklarini topish
        viewed_news_ids = user.viewednews.values_list("news", flat=True)
        latest_news = (
            cls.objects.exclude(id__in=viewed_news_ids)
            .filter(active=True)
            .order_by("-start_date")
            .first()
        )
        return latest_news


class ViewedNews(TimeStampedModel, models.Model):
    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="viewednews"
    )
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="viewednews")

    def __str__(self) -> str:
        return self.user.full_name


class Favorite(TimeStampedModel, models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(
        "product.ProductItem", on_delete=models.CASCADE, related_name="favorite"
    )

    class Meta:
        unique_together = ("user", "product")

    def __str__(self) -> str:
        return f"{self.user.origin.username} - {self.product.desc}"


class Banner(TimeStampedModel, models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="media/banner")
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    name = models.CharField(max_length=255)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)  # Oddiy narx
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2)  # Optom narx
    min_wholesale_quantity = models.IntegerField(default=10)  # Minimal optom miqdori

    def __str__(self):
        return self.name
