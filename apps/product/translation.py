from modeltranslation.translator import register, TranslationOptions
from .models import Category, ProductItem, Ticket, Phone, Good, Image, SoldProduct


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'desc')



@register(Ticket)
class TicketTranslationOptions(TranslationOptions):
    fields = ('event_name',)


@register(ProductItem)
class ProductItemTranslationOptions(TranslationOptions):
    fields = ('desc',)


@register(Phone)
class PhoneTranslationOptions(TranslationOptions):
    fields = ('model_name', )


@register(Good)
class GoodTranslationOptions(TranslationOptions):
    fields = ('name', 'ingredients')


@register(Image)
class ImageTranslationOptions(TranslationOptions):
    fields = ('name', )

