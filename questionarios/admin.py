from django.contrib import admin, messages

from .exceptions import ErroDeQuestionario
from .forms import AlternativasFormSet, QuestaoAdminForm
from .models import Alternativa, Questao, Tentativa
from .services import QuestaoService


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    formset = AlternativasFormSet
    fields = ("texto", "correta")
    min_num = 2
    max_num = 5
    extra = 0


@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    """Questões de cada aula (RF014). Gravação e exclusão passam pelo QuestaoService."""

    form = QuestaoAdminForm
    inlines = (AlternativaInline,)
    list_display = ("aula", "posicao", "enunciado")
    list_display_links = ("enunciado",)
    list_filter = ("aula",)
    search_fields = ("enunciado",)
    list_select_related = ("aula",)
    ordering = ("aula__modulo__posicao", "aula__posicao", "posicao")
    autocomplete_fields = ("sinal",)
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        QuestaoService.salvar(obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        if obj is not None:
            try:
                QuestaoService.validar_exclusao(obj)
            except ErroDeQuestionario:
                return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        QuestaoService.excluir(obj)

    def delete_queryset(self, request, queryset):
        for questao in queryset.select_related("aula"):
            try:
                QuestaoService.excluir(questao)
            except ErroDeQuestionario as exc:
                self.message_user(request, f"“{questao}” não foi excluída: {exc.mensagem}", messages.ERROR)


@admin.register(Tentativa)
class TentativaAdmin(admin.ModelAdmin):
    """Consulta das tentativas, somente leitura, enquanto o RF012 está fora do escopo."""

    list_display = ("realizada_em", "aluno", "aula", "acertos", "total", "percentual", "aprovada")
    list_filter = ("aprovada",)
    list_select_related = ("aluno", "aula")
    list_per_page = 20

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
