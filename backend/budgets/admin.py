from django.contrib import admin

from .models import LineItem, Scenario

admin.site.register(Scenario)
admin.site.register(LineItem)
