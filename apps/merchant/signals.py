from datetime import timedelta

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, OrderItem, LoyaltyCard, LoyaltyPendingBonus
from ..customer.models import Profile


@receiver(m2m_changed, sender=Order.products.through)
def update_order_total(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.update_total_amount()
        





@receiver(post_save, sender=Order)
def create_pending_bonus(sender, instance, created, **kwargs):
    """
    Создаём LoyaltyPendingBonus ТОЛЬКО когда Order стал PAID/SENT
    """

    if instance.status not in ["approved", "check_pending"]:
        return

    # ❗ чтобы не создавать повторно
    if LoyaltyPendingBonus.objects.filter(order=instance).exists():
        return

    if instance.total_amount <= 0:
        return

    LoyaltyPendingBonus.objects.create(
        profile=instance.user,
        order=instance,
        order_name=f"Заказ #{instance.id}",
        order_amount=instance.total_amount,
        status="pending"
    )


@receiver(post_save, sender=Profile)
def create_loyalty_card(sender, instance, created, **kwargs):
    """
    Автоматически создаёт LoyaltyCard
    при создании Profile
    """
    if not created:
        return

    today = timezone.now().date()

    LoyaltyCard.objects.create(
        profile=instance,
        cycle_start=today,
        cycle_end=today + timedelta(days=60),
        cycle_number=1
    )

@receiver(post_save, sender=LoyaltyPendingBonus)
def update_loyalty_card_balance(sender, instance, created, **kwargs):

    # Условия начисления
    if instance.status == "approved" and instance.bonus_amount > 0:
        card, _ = LoyaltyCard.objects.get_or_create(
            profile=instance.profile
        )

        card.current_balance += instance.bonus_amount
        card.save()


