from django.contrib import admin
from django.utils.html import format_html

from .forms.admin import CategoriaAdminForm, SinalAdminForm
from .models import Categoria, Sinal
from .services import CategoriaService, DicionarioService, SinalService


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Categorias do dicionário (RF015). A gravação passa pelo CategoriaService."""

    form = CategoriaAdminForm
    list_display = ("nome", "ativa")
    list_filter = ("ativa",)
    search_fields = ("nome",)
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        CategoriaService.salvar(obj)


@admin.register(Sinal)
class SinalAdmin(admin.ModelAdmin):
    """Sinais do dicionário (RF015). A gravação passa pelo SinalService."""

    form = SinalAdminForm
    list_display = ("termo", "categoria", "classe_gramatical", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("termo",)
    search_help_text = "Pesquise por parte do termo, com ou sem acentos."
    list_select_related = ("categoria",)
    list_per_page = 20
    readonly_fields = ("previa_do_video",)

    @admin.display(description="Prévia do vídeo")
    def previa_do_video(self, obj: Sinal) -> str:
        if not obj.video:
            return "—"
        return format_html(
            '<video src="{}" controls loop muted playsinline width="320"></video>', obj.video.url
        )

    def get_search_results(self, request, queryset, search_term):
        return DicionarioService.filtrar(queryset, search_term), False

    def save_model(self, request, obj, form, change):
        SinalService.salvar(obj)
