from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .forms import AulaAdminForm, ModuloAdminForm
from .models import Aula, AvaliacoesDaAula, MaterialComplementar, Modulo
from .services import AulaService, AvaliacaoService, ModuloService


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


@admin.register(AvaliacoesDaAula)
class AvaliacoesDaAulaAdmin(admin.ModelAdmin):
    """Médias e comentários das avaliações por aula, sem dados do aluno (RF018, RS004)."""

    list_display = ("modulo", "titulo", "publicada", "media_das_notas", "quantidade")
    list_select_related = ("modulo",)
    search_fields = ("titulo",)
    ordering = ("modulo__posicao", "posicao")
    list_per_page = 20
    fields = ("modulo", "titulo", "media_das_notas", "quantidade", "comentarios")
    readonly_fields = fields

    def get_queryset(self, request):
        return AvaliacaoService.com_resumo(super().get_queryset(request))

    # Não pode se chamar "media": o ModelAdmin já usa esse nome para os arquivos CSS e JS.
    @admin.display(description="média", ordering="media_avaliacoes")
    def media_das_notas(self, aula):
        media = AvaliacaoService.arredondar(getattr(aula, "media_avaliacoes", None))
        return "—" if media is None else str(media).replace(".", ",")

    @admin.display(description="avaliações", ordering="quantidade_avaliacoes")
    def quantidade(self, aula):
        return getattr(aula, "quantidade_avaliacoes", 0)

    @admin.display(description="comentários")
    def comentarios(self, aula):
        resumo = AvaliacaoService.resumo(aula)
        if not resumo.quantidade:
            return "Esta aula ainda não possui avaliações"
        if not resumo.comentarios:
            return "Nenhum comentário"
        # format_html_join escapa o texto enviado pelos alunos (RS013).
        itens = format_html_join(
            "",
            "<li>{} · {} de 5 · {}</li>",
            ((data.strftime("%d/%m/%Y"), nota, texto) for data, nota, texto in resumo.comentarios),
        )
        return format_html("<ul>{}</ul>", itens)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
