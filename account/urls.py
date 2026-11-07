from django.urls import path
from . import views

urlpatterns = [
    path('me', views.me),
    path('edit', views.edit_account),
    path("confirm-email", views.confirm_email),
]