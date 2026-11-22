from django.contrib import admin
from django.urls import reverse

from .forms import AulaAdminForm, ModuloAdminForm
from .models import Aula, MaterialComplementar, Modulo
from .services import AulaService, ModuloService


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    """Módulos da trilha (RF013). A gravação passa pelo ModuloService."""

    form = ModuloAdminForm
    list_display = ("posicao", "titulo")
    list_display_links = ("titulo",)
    search_fields = ("titulo",)
    ordering = ("posicao",)
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        ModuloService.salvar(obj)


class MaterialComplementarInline(admin.TabularInline):
    model = MaterialComplementar
    extra = 0
    fields = ("titulo", "arquivo")


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    """Aulas da trilha (RF013). A gravação e a publicação passam pelo AulaService."""

    form = AulaAdminForm
    inlines = (MaterialComplementarInline,)
    list_display = ("titulo", "modulo", "posicao", "publicada")
    list_filter = ("modulo", "publicada")
    search_fields = ("titulo",)
    list_select_related = ("modulo",)
    ordering = ("modulo__posicao", "posicao")
    list_per_page = 20

    def view_on_site(self, obj: Aula) -> str:
        # O administrador vê a aula como o aluno, mesmo antes de publicar (RF013).
        return reverse("trilha:aula", args=[obj.pk])

    def save_model(self, request, obj, form, change):
        AulaService.salvar(obj)
