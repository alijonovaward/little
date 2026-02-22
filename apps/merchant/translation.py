from modeltranslation.translator import register, TranslationOptions
from .models import Order, OrderItem, Information


# @register(OrderItem)
# class ConnectTranslationOptions(TranslationOptions):
#     fields = ('order__product__desc',)
@register(Information)
class InformationTranslationOptions(TranslationOptions):
    fields = ('reminder', 'agreement', 'shipment_terms',
              'privacy_policy', 'about_us', 'support_center', 'payment_data')
