import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.customer.models import News
from .models import ProductItem

FCM_URL = "https://fcm.googleapis.com/fcm/send"
FCM_SERVER_KEY = settings.FCM_SERVER_KEY


def send_fcm_notification(title, body, topic):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"key={FCM_SERVER_KEY}",
    }
    data = {
        "to": f"/topics/all",
        "priority": "high",
        "notification": {"title": title, "body": body},
    }
    requests.post(FCM_URL, json=data, headers=headers)
    # return response.json()


@receiver(post_save, sender=News)
def news_created(sender, instance, created, **kwargs):
    if created:
        send_fcm_notification("Yangilik!", instance.title, "newsTopic")


@receiver(post_save, sender=ProductItem)
def product_created(sender, instance, created, **kwargs):
    if created:
        send_fcm_notification("Yangi mahsulot!", instance.desc, "productTopic")
        # pass


@receiver(post_save, sender=ProductItem)
def product_price_changed(sender, instance, **kwargs):
    if instance.price_changed():  # Bu metod narx o'zgarganligini aniqlash uchun
        send_fcm_notification("Mahsulot narxi arzonladi", instance.desc, "productTopic")
