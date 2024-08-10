# translation.py en tu aplicación, por ejemplo, en apps/authentication

from django.contrib.auth.models import Group
from modeltranslation.translator import TranslationOptions, register


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = ("name",)
