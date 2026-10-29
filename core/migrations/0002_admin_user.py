"""Grant admin rights to the portal administrator.

The user logs in through Active Directory (brembana-auth), which never touches
the ``is_staff`` and ``is_superuser`` flags: setting them once here is enough.
If the user has not logged in yet, it is created without a local password and
the first AD login fills in name, email and profile.
"""

from django.db import migrations

ADMIN_USERNAMES = ["plitta"]


def grant_admin(apps, schema_editor):
    User = apps.get_model("auth", "User")
    for username in ADMIN_USERNAMES:
        user, created = User.objects.get_or_create(username=username)
        if created:
            # Same marker Django uses for set_unusable_password(): AD login only.
            user.password = "!"
        user.is_staff = True
        user.is_superuser = True
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(grant_admin, migrations.RunPython.noop),
    ]
