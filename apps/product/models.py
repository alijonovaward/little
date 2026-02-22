import uuid
from django.db import models
from model_utils.models import TimeStampedModel


class Category(TimeStampedModel, models.Model):
    PRODUCT_TYPE = (
        ("f", "Oziq-ovqat"),
    )
    main_type = models.CharField(max_length=1, choices=PRODUCT_TYPE, default="f")
    name = models.CharField(blank=True, max_length=255)
    image = models.ImageField(upload_to="category")
    desc = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    def get_type_display(self):
        """Get the human-readable main_type label."""
        return dict(self.PRODUCT_TYPE).get(self.main_type, "Unknown")


class ProductItem(TimeStampedModel, models.Model):
    CHOICES = (
        (0, "KG"),
        (1, "DONA"),
        (2, "L"),
        (3, "PAKET"),
    )
    desc = models.TextField()
    product_type = models.UUIDField(default=uuid.uuid4, editable=True)

    # CHAKANA NARXLAR
    old_price = models.DecimalField(
        decimal_places=0, max_digits=10, null=True, blank=True, default=0
    )
    new_price = models.DecimalField(
        decimal_places=0, max_digits=10, null=True, blank=True, default=0
    )

    # B2B NARX
    b2b_price = models.DecimalField(
        decimal_places=0,
        max_digits=10,
        null=True,
        blank=True,
        default=0,
        help_text="B2B (company) mijozlar uchun narx (user.is_b2b=True bo'lsa)",
    )

    min_wholesale_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Optom narxda olish uchun minimal miqdor"
    )

    weight = models.FloatField(default=1, null=True, blank=True)
    measure = models.IntegerField(choices=CHOICES, default=0, null=True, blank=True)
    available_quantity = models.PositiveIntegerField(default=0)
    # discountprice
    bonus = models.IntegerField(default=0, null=True, blank=True)
    discount_price = models.IntegerField(default=0, null=True, blank=True)
    main = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['product_type']),
        ]

    @property
    def variants(self):
        return ProductItem.objects.filter(product_type=self.product_type).exclude(id=self.id)

    @property
    def sale(self):
        if not self.old_price or not self.new_price or self.new_price >= self.old_price:
            return 0
        return round((1 - (self.new_price / self.old_price)) * 100)

    def price_changed(self):
        return self.old_price > self.new_price

    def __str__(self) -> str:
        return f"{self.desc[:30]}"

    def get_measure_display(self):
        return dict(self.CHOICES).get(self.measure, "Unknown")


class Ticket(models.Model):
    event_name = models.CharField(max_length=255)
    product = models.OneToOneField(
        ProductItem, on_delete=models.CASCADE, related_name="tickets"
    )
    event_date = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="tickets"
    )

    def __str__(self) -> str:
        return self.event_name

    def save(self, *args, **kwargs):
        self.product.measure = 1
        self.product.save()
        super().save(*args, **kwargs)


class Phone(models.Model):
    STORAGE = (
        ("16 GB", "16 GB"), ("32 GB", "32 GB"), ("64 GB", "64 GB"),
        ("128 GB", "128 GB"), ("256 GB", "256 GB"), ("512 GB", "512 GB"),
        ("1 TB", "1 TB"), ("2 TB", "2 TB"), ("other", "Boshqa"),
    )
    RAM = (
        ("2 GB", "2 GB"), ("4 GB", "4 GB"), ("6 GB", "6 GB"),
        ("8 GB", "8 GB"), ("12 GB", "12 GB"), ("16 GB", "16 GB"),
        ("32 GB", "32 GB"), ("64 GB", "64 GB"), ("other", "Boshqa"),
    )
    COLOR_CHOICES = (
        ("red", "Red"), ("blue", "Blue"), ("pink", "Pink"),
        ("green", "Green"), ("black", "Black"), ("white", "White"),
        ("gold", "Gold"), ("silver", "Silver"), ("other", "Boshqa"),
    )
    CONDITION = (
        ("good", "Yaxshi"), ("exc", "A'lo"),
        ("used", "Foydalanilgan"), ("new", "Yangi"),
    )
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default="black")
    condition = models.CharField(max_length=10, choices=CONDITION, default="new")
    product = models.OneToOneField(
        ProductItem, on_delete=models.CASCADE, related_name="phones"
    )
    model_name = models.CharField(max_length=255)
    ram = models.CharField(max_length=255, choices=RAM, default=0)
    storage = models.CharField(max_length=255, choices=STORAGE, default=0)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="phones"
    )

    def __str__(self) -> str:
        return self.model_name

    def save(self, *args, **kwargs):
        self.product.measure = 1
        self.product.save()
        super().save(*args, **kwargs)


class Good(models.Model):
    name = models.CharField(max_length=255)
    product = models.OneToOneField(
        ProductItem, on_delete=models.CASCADE, related_name="goods", null=True, blank=True
    )
    ingredients = models.CharField(max_length=255, null=True, blank=True)
    expire_date = models.DateField(null=True, blank=True)
    # SubCategory o'rniga Category ga ulandi
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods"
    )

    def __str__(self) -> str:
        return self.name


class Image(models.Model):
    image = models.ImageField(upload_to="images", null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    product = models.ForeignKey(
        ProductItem, on_delete=models.CASCADE, related_name="images"
    )

    def __str__(self) -> str:
        return self.name


class SoldProduct(TimeStampedModel, models.Model):
    product = models.ForeignKey(
        ProductItem, on_delete=models.SET_NULL, null=True, related_name="sold_products"
    )
    user = models.ForeignKey("customer.Profile", on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(decimal_places=0, default=0, max_digits=20)
    quantity = models.PositiveIntegerField(default=0)

    def __int__(self) -> int:
        return self.id
