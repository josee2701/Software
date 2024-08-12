# translation.py en tu aplicación, por ejemplo, en apps/authentication

from django.contrib.auth.models import Group
from modeltranslation.translator import TranslationOptions, register

from apps.realtime.models import Brands_assets, Line_assets, Types_assets


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Types_assets)
class Types_assetsTranslationOptions(TranslationOptions):
    fields = ("asset_name",)
    
@register(Brands_assets)
class Brands_assetsTranslationOptions(TranslationOptions):
    fields = ("brand",)
    
@register(Line_assets)
class Line_assetsTranslationOptions(TranslationOptions):
    fields = ("line",)