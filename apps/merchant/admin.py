from django.contrib import admin
from .models import *


class InformationAdmin(admin.ModelAdmin):
    list_display = [
        "reminder",
        "agreement",
        "shipment_terms",
        "privacy_policy",
        "about_us",
        "support_center",
        "payment_data",
    ]


class ServiceAdmin(admin.ModelAdmin):
    list_display = ["delivery_fee"]
admin.site.register(Service, ServiceAdmin)


class SocialMediaAdmin(admin.ModelAdmin):
    list_display = ["telegram", "instagram", "whatsapp", "phone_number", "imo", "kakao"]
admin.site.register(SocialMedia, SocialMediaAdmin)


admin.site.register(Information, InformationAdmin)
class BonusaAdmin(admin.ModelAdmin):
    list_display = ["amount", "percentage", "title", "created", "modified", 'active']
admin.site.register(Bonus, BonusaAdmin)

admin.site.register(OrderItem)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Agar siz yangi Order yaratayotganda bitta bo'sh OrderItem qo'shmoqchi bo'lsangiz


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ("user", "status", "total_amount", "loyalty_payment", "created_at")
    search_fields = ("user__full_name", "status")
    list_filter = ("status",)

admin.site.register(Order, OrderAdmin)


@admin.register(LoyaltyCard)
class LoyaltyCardModelAdmin(admin.ModelAdmin):
    list_display = ['profile','current_balance','cycle_start','cycle_end','cycle_days','cycle_number','created_at','updated_at']



@admin.register(LoyaltyPendingBonus)
class LoyaltyPendingBonusAdmin(admin.ModelAdmin):
    list_display = [
        "order_name",
        "profile",
        "order_amount",
        "percent",
        "bonus_amount",
        "status",
        "created_at",
    ]

    list_editable = ["percent", "status"]

    readonly_fields = [
        "order",
        "order_name",
        "order_amount",
        "bonus_amount",
        "profile",
    ]


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referee', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['approve_referral_bonus']

    def approve_referral_bonus(self, request, queryset):
        for ref in queryset:
            if ref.status == 'pending':
                ref.status = 'rewarded'  # Меняем статус
                ref.save()  # Это само вызовет нашу логику из метода save()



# WalletTransaction admin removed - model no longer exists


admin.site.register(BankCardModel)