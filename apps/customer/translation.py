from modeltranslation.translator import register, TranslationOptions
from .models import Profile, Location, News, ViewedNews, Favorite


@register(News)
class ConnectTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
