from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from .models import Category, ProductItem, Good, Phone, Ticket, Image, SoldProduct


# ==========================================
# 1. INLINES (Bitta sahifada chiqarish uchun)
# ==========================================

class ImageInline(admin.TabularInline):
    model = Image
    extra = 1

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Agar yangi mahsulot qo'shilayotgan bo'lsa (yoki Save as new bo'lsa),
        # eski rasmlarni ko'rsatmaymiz, shunda ular yangisiga bog'lanib qolmaydi
        if "/add/" in request.path or "_saveasnew" in request.path:
            return queryset.none()
        return queryset


class GoodInline(admin.StackedInline):
    model = Good
    extra = 0
    max_num = 1


class PhoneInline(admin.StackedInline):
    model = Phone
    extra = 0
    max_num = 1


class TicketInline(admin.StackedInline):
    model = Ticket
    extra = 0
    max_num = 1


# ==========================================
# 2. ASOSIY ADMINLAR
# ==========================================

@admin.register(Category)
class CategoryAdmin(TranslationAdmin):  # Tarjimalar bilan
    list_display = ("preview", "name", "main_type", "active", "created")
    list_filter = ("main_type", "active")
    search_fields = ("name",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 45px; height: 45px; border-radius: 50%;" />', obj.image.url)
        return "-"


@admin.register(ProductItem)
class ProductItemAdmin(TranslationAdmin):
    list_display = [
        "get_thumbnail",
        "get_product_name",
        "new_price",
        "old_price",
        "available_quantity",
        "product_type",
        "main",
        "active",
    ]
    list_filter = ["active", "main", "measure", "created"]
    search_fields = ["desc", "product_type", "goods__name", "phones__model_name"]
    list_editable = ["active", "main", "new_price", "available_quantity"]

    # HAMMA NARSA BIR JOYDA:
    inlines = [GoodInline, ImageInline]

    # Variant qo'shishni osonlashtiradi:
    save_as = True
    save_on_top = True

    def save_formset(self, request, form, formset, change):
        # Agar "Save as new" tugmasi bosilgan bo'lsa
        if '_saveasnew' in request.POST:
            # Formset ichidagi barcha obyektlarni (rasmlarni)
            # yangi obyekt deb hisoblashini oldini olamiz
            instances = formset.save(commit=False)
            for instance in instances:
                # Agar bu Image modeli bo'lsa va yangi mahsulot yaratilayotgan bo'lsa
                # Biz faqat YANGI yuklangan rasmlarni saqlashimiz kerak
                if not instance.pk:
                    instance.save()
            formset.save_m2m()
        else:
            # Oddiy saqlash holati
            formset.save()

    def get_thumbnail(self, obj):
        # Mahsulotning birinchi rasmini ro'yxatda chiqarish
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 5px;" />',
                               first_image.image.url)
        return "-"

    get_thumbnail.short_description = "Rasm"

    def get_product_name(self, obj):
        # Qaysi modelga ulangan bo'lsa o'sha yerdagi nomini oladi
        if hasattr(obj, 'goods'): return obj.goods.name
        if hasattr(obj, 'phones'): return obj.phones.model_name
        if hasattr(obj, 'tickets'): return obj.tickets.event_name
        return "Nomsiz"

    get_product_name.short_description = "Mahsulot nomi"


@admin.register(SoldProduct)
class SoldProductAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "quantity", "amount", "created"]
    list_filter = ["created"]
    readonly_fields = ["user", "product", "quantity", "amount"]  # Sotilgan narsani o'zgartirib bo'lmasin


# Alohida modellarni ham qoldiramiz (kerak bo'lib qolsa)
@admin.register(Good)
class GoodAdmin(TranslationAdmin):
    list_display = ["name", "category", "expire_date"]
    search_fields = ["name"]


@admin.register(Phone)
class PhoneAdmin(TranslationAdmin):
    list_display = ["model_name", "category", "ram", "storage", "color"]
    search_fields = ["model_name"]
