from django.contrib import admin

from .models import Event, EventFeature

models = [Event, EventFeature]
admin.site.register(models)
