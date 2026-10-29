"""Tests of the frontend app: login flow and access protection."""

from unittest.mock import patch

from brembana_auth.ldap_client import ADUser
from brembana_auth.models import ADProfile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

AD_USER = ADUser(
    dn="CN=Paolo Litta,OU=Users,DC=brembana,DC=dom",
    username="plitta",
    first_name="Paolo",
    last_name="Litta",
    email="plitta@brembanarolle.com",
    title="AI Engineer",
    description="BR135",
)


class AccessTests(TestCase):
    """Anonymous visitors are sent to the login page; the API answers 401."""

    def test_index_redirects_anonymous_to_login(self):
        response = self.client.get(reverse("index"))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_api_rejects_anonymous_with_401(self):
        response = self.client.get("/api/machines/")
        self.assertEqual(response.status_code, 401)

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Accedi con le credenziali del dominio")
        self.assertContains(response, 'name="username"')


class LoginTests(TestCase):
    """Login through the AD backend (LDAP mocked) and through the local fallback."""

    @patch("brembana_auth.backend.ldap_authenticate", return_value=AD_USER)
    def test_ad_login_creates_user_and_profile(self, ldap_authenticate):
        response = self.client.post(
            reverse("login"),
            {"username": "plitta@brembanarolle.com", "password": "secret"},
        )
        self.assertRedirects(response, reverse("index"))
        ldap_authenticate.assert_called_once_with("plitta@brembanarolle.com", "secret")

        user = get_user_model().objects.get(username="plitta")
        self.assertEqual(user.get_full_name(), "Paolo Litta")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(ADProfile.objects.get(user=user).title, "AI Engineer")

        page = self.client.get(reverse("index"))
        self.assertContains(page, "Paolo Litta")
        self.assertContains(page, "AI Engineer")
        self.assertEqual(self.client.get("/api/machines/").status_code, 200)

    @patch("brembana_auth.backend.ldap_authenticate", return_value=None)
    def test_wrong_credentials_show_error(self, ldap_authenticate):
        response = self.client.post(
            reverse("login"),
            {"username": "plitta@brembanarolle.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Utente o password non corretti.")
        self.assertEqual(self.client.get(reverse("index")).status_code, 302)

    @patch("brembana_auth.backend.ldap_authenticate", return_value=None)
    def test_local_account_falls_back_to_model_backend(self, ldap_authenticate):
        get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
        response = self.client.post(reverse("login"), {"username": "admin", "password": "pw"})
        self.assertRedirects(response, reverse("index"))

    def test_logout_redirects_to_login_and_ends_session(self):
        user = get_user_model().objects.create_user("local", password="pw")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(self.client.get("/api/machines/").status_code, 401)


class AdminUserTests(TestCase):
    """The portal administrator gets admin rights from the data migration."""

    @patch("brembana_auth.backend.ldap_authenticate", return_value=AD_USER)
    def test_plitta_is_superuser_after_ad_login(self, ldap_authenticate):
        user = get_user_model().objects.get(username="plitta")
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertFalse(user.has_usable_password())

        self.client.post(reverse("login"), {"username": "plitta", "password": "secret"})
        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), "Paolo Litta")
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
