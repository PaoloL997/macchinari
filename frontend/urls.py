"""URLs of the frontend app."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import IndexView, LoginView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
