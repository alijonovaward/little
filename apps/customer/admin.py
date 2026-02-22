from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from modeltranslation.admin import TranslationAdmin
from .models import *

# Register your models here.
class NewsAdmin(TranslationAdmin):
    list_display=['start_date','title', 'end_date', 'description']

class BannerAdmin(admin.ModelAdmin):
    list_display=['title', 'active']

class LocationAdmin(admin.ModelAdmin):
    list_display=['user', 'address']

class ProfileAdmin(admin.ModelAdmin):
    list_display=['phone_number','full_name']

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(ViewedNews)
admin.site.register(Favorite)
admin.site.register(Banner, BannerAdmin)


class CustomUserAdmin(UserAdmin):
    # Добавляем новые поля в список отображения (в таблице)
    list_display = ('username' ,'is_wholesaler', 'is_approved', 'is_b2b', 'is_staff', 'img')

    # Добавляем новые поля в форму редактирования (когда нажал на юзера)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('img', 'is_wholesaler', 'is_approved', 'is_b2b')}),
    )

    # Добавляем новые поля в форму создания (когда нажимаешь "Add User")
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('img', 'is_wholesaler', 'is_approved', 'is_b2b')}),
    )




    @admin.action(description="Tanlanganlarni optomchi sifatida tasdiqlash")
    def approve_wholesalers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} ta foydalanuvchi tasdiqlandi.")

    @admin.action(description="Tanlanganlardan optomchi maqomini olib tashlash")
    def unapprove_wholesalers(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} ta foydalanuvchidan tasdiq olib tashlandi.")

# Регистрируем модель с новыми настройками
admin.site.register(User, CustomUserAdmin)


@admin.register(B2BApplication)
class B2BApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company_name", "phone", "status", "created")
    list_filter = ("status",)
    search_fields = ("company_name", "phone", "user__username")

    @admin.action(description="B2B arizalarni APPROVED qilish")
    def approve_b2b(self, request, queryset):
        # queryset.update(...) save() ni chaqirmaydi.
        # Bizda esa save() ichida: status=approved bo'lsa -> user.is_b2b=True bo'ladi.
        updated = 0
        for application in queryset.select_related("user"):
            application.status = B2BApplication.Status.APPROVED
            application.save()
            updated += 1

        self.message_user(request, f"{updated} ta B2B ariza approved qilindi")

    @admin.action(description="B2B arizalarni REJECTED qilish")
    def reject_b2b(self, request, queryset):
        updated = 0
        for application in queryset:
            application.status = B2BApplication.Status.REJECTED
            application.save()
            updated += 1

        self.message_user(request, f"{updated} ta B2B ariza rejected qilindi")

    actions = [approve_b2b, reject_b2b]