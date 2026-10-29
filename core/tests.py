"""Tests of the core app: admin pages."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Machine, Operation, Plant


class AdminTests(TestCase):
    """Every registered admin page renders for a superuser."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        plant = Plant.objects.create(name="Bergamo")
        cls.machine = Machine.objects.create(
            name="Pressa 1",
            plant=plant,
            agent_url="http://100.64.0.1:8000",
            agent_token="t",
            manifest={"capabilities": {"files": {"accept": [".pcn"]}, "status": {}}},
        )
        Operation.objects.create(
            machine=cls.machine, user=cls.admin, action="upload", filename="a.pcn", success=True
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_changelists_render(self):
        for url_name in [
            "admin:core_plant_changelist",
            "admin:core_machine_changelist",
            "admin:core_operation_changelist",
            "admin:brembana_auth_adprofile_changelist",
        ]:
            with self.subTest(url_name=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_machine_changelist_shows_capabilities(self):
        response = self.client.get(reverse("admin:core_machine_changelist"))
        self.assertContains(response, "files, status")

    def test_machine_change_page_renders(self):
        url = reverse("admin:core_machine_change", args=[self.machine.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_operations_are_read_only(self):
        operation = Operation.objects.first()
        url = reverse("admin:core_operation_change", args=[operation.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:core_operation_add")).status_code, 403)
