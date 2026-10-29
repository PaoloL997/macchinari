"""Admin configuration of the portal: plants, machines, operations and AD profiles."""

from brembana_auth.models import ADProfile
from django.contrib import admin, messages
from django.db.models import Count
from django.utils.html import format_html

from .client import AgentClient, AgentError
from .models import Machine, Operation, Plant
from .schemas import Manifest

admin.site.site_header = "Brembana&Rolle / Macchinari"
admin.site.site_title = "Macchinari"
admin.site.index_title = "Amministrazione"


class MachineInline(admin.TabularInline):
    """Machines of a plant, listed on the plant page."""

    model = Machine
    fields = ["name", "description", "active"]
    show_change_link = True
    extra = 0


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """Plants and how many machines each one has."""

    list_display = ["name", "machine_count"]
    search_fields = ["name"]
    inlines = [MachineInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_machine_count=Count("machines"))

    @admin.display(description="Macchinari", ordering="_machine_count")
    def machine_count(self, plant: Plant) -> int:
        return plant._machine_count


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    """Machines, their agent connection and the manifest read from the agent."""

    list_display = ["name", "plant", "active", "capability_list", "agent_url"]
    list_filter = ["active", "plant"]
    search_fields = ["name", "description", "agent_url"]
    list_select_related = ["plant"]
    actions = ["fetch_manifest"]
    fieldsets = [
        (None, {"fields": ["name", "description", "plant", "illustration", "active"]}),
        ("Agente", {"fields": ["agent_url", "agent_token"]}),
        (
            "Manifest",
            {
                "fields": ["manifest"],
                "description": (
                    "Descrizione delle capacità esposte dall'agente. "
                    "Usa l'azione «Aggiorna manifest dall'agente» per leggerla dalla macchina."
                ),
            },
        ),
    ]

    @admin.display(description="Capacità")
    def capability_list(self, machine: Machine) -> str:
        try:
            caps = machine.parsed_manifest.capabilities.model_dump()
        except Exception:
            return format_html('<span style="color:#b91c1c">manifest non valido</span>')
        names = [name for name, config in caps.items() if config is not None]
        return ", ".join(names) or "—"

    @admin.action(description="Aggiorna manifest dall'agente")
    def fetch_manifest(self, request, queryset):
        """Read GET /manifest from the agent of each selected machine and store it."""
        for machine in queryset:
            try:
                manifest = AgentClient(machine).get("/manifest", Manifest)
            except AgentError as e:
                self.message_user(request, str(e), level=messages.ERROR)
                continue
            machine.manifest = manifest.model_dump()
            machine.save(update_fields=["manifest"])
            self.message_user(request, f"{machine.name}: manifest aggiornato.", level=messages.SUCCESS)


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    """Read-only log of the file operations performed through the portal."""

    list_display = ["timestamp", "machine", "user", "action", "filename", "success"]
    list_filter = ["action", "success", "machine__plant", "machine"]
    search_fields = ["filename", "detail", "user__username", "machine__name"]
    date_hierarchy = "timestamp"
    list_select_related = ["machine", "machine__plant", "user"]
    readonly_fields = ["machine", "user", "action", "filename", "success", "detail", "timestamp"]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(ADProfile)
class ADProfileAdmin(admin.ModelAdmin):
    """Read-only view of the Active Directory data synced at every login."""

    list_display = ["user", "full_name", "title", "pc_code", "last_sync"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email"]
    readonly_fields = ["user", "title", "pc_code", "last_sync"]
    list_select_related = ["user"]

    @admin.display(description="Nome", ordering="user__last_name")
    def full_name(self, profile: ADProfile) -> str:
        return profile.user.get_full_name()

    def has_add_permission(self, request) -> bool:
        """Profiles are created by the login backend, never by hand."""
        return False
