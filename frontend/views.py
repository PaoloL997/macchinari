"""Views of the frontend app."""

from django import forms
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


class LoginForm(AuthenticationForm):
    """Login form with the domain credentials.

    The ``username`` field accepts anything brembana-auth understands (email,
    email alias, UPN or username), so it is labelled generically as "Utente".
    """

    username = forms.CharField(
        label="Utente",
        max_length=254,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "class": "text-input login__input",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "text-input login__input",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Utente o password non corretti.",
        "inactive": "Questo account è disattivato.",
    }


class LoginView(auth_views.LoginView):
    """Login page: domain credentials verified through brembana-auth."""

    template_name = "frontend/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True


@method_decorator(ensure_csrf_cookie, name="dispatch")
class IndexView(LoginRequiredMixin, TemplateView):
    """Render the single page of the portal, for logged-in users only.

    The ``csrftoken`` cookie is always set so that the JavaScript client can
    send the ``X-CSRFToken`` header on POST and DELETE requests to the API.
    """

    template_name = "frontend/index.html"
