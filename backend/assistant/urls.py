from django.urls import path

from . import views

urlpatterns = [
    path("scenarios/<int:scenario_id>/chat/", views.chat, name="chat"),
]
