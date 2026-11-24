from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

from .documentos import Cpf
from .models import RegistroAuditoria, ResponsavelLegal, Usuario
from .services import AuditoriaService, UsuarioService

CAMPOS_DO_ALUNO = (
    "nome_completo",
    "email",
    "cpf_parcial",
    "data_nascimento",
    "data_cadastro",
    "is_active",
)


class ResponsavelLegalInline(admin.StackedInline):
    """Responsável do aluno menor, somente para leitura (RF002, RF016)."""

    model = ResponsavelLegal
    fields = ("nome", "vinculo", "cpf_parcial", "email", "telefone", "termo_aceito_em")
    readonly_fields = fields
    can_delete = False
    extra = 0
    max_num = 0

    @admin.display(description="CPF")
    def cpf_parcial(self, obj: ResponsavelLegal) -> str:
        return Cpf.de_texto(obj.cpf).parcial

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """Consulta de alunos (RF016). A deficiência nunca é exibida (RNF006)."""

    list_display = CAMPOS_DO_ALUNO
    list_filter = ("is_active",)
    search_fields = ("nome_completo", "email")
    search_help_text = "Pesquise por parte do nome, e-mail ou CPF completo."
    list_per_page = 20
    fields = CAMPOS_DO_ALUNO
    readonly_fields = CAMPOS_DO_ALUNO
    actions = ("desativar_selecionados", "reativar_selecionados")
    inlines = (ResponsavelLegalInline,)

    @admin.display(description="CPF")
    def cpf_parcial(self, obj: Usuario) -> str:
        return Cpf.de_texto(obj.cpf).parcial if obj.cpf else "—"

    def get_queryset(self, request):
        return UsuarioService.alunos()

    def get_search_results(self, request, queryset, search_term):
        return UsuarioService.buscar_alunos(queryset, search_term), False

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        resposta = super().change_view(
            request,
            object_id,
            form_url,
            extra_context={
                **(extra_context or {}),
                "show_save": False,
                "show_save_and_continue": False,
                "show_save_and_add_another": False,
                "show_delete": False,
            },
        )
        aluno = self.get_object(request, object_id)
        if request.method == "GET" and aluno is not None:
            AuditoriaService.registrar(
                request.user, RegistroAuditoria.Acao.CONSULTA_ALUNO, alvo=aluno
            )
        return resposta

    @admin.action(description="Desativar usuários selecionados", permissions=("change",))
    def desativar_selecionados(self, request, queryset):
        if request.POST.get("confirmacao") != "sim":
            contexto = {
                **self.admin_site.each_context(request),
                "title": "Desativar usuários",
                "opts": self.model._meta,
                "alunos": queryset,
                "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            }
            return TemplateResponse(
                request, "admin/contas/usuario/confirmar_desativacao.html", contexto
            )
        for aluno in queryset:
            UsuarioService.desativar(aluno, por=request.user)
        self.message_user(request, "Usuário desativado com sucesso", messages.SUCCESS)
        return None

    @admin.action(description="Reativar usuários selecionados", permissions=("change",))
    def reativar_selecionados(self, request, queryset):
        for aluno in queryset:
            UsuarioService.reativar(aluno, por=request.user)
        self.message_user(request, "Usuário reativado com sucesso", messages.SUCCESS)


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Registros somente leitura (RS004, RS009)."""

    list_display = ("criado_em", "autor", "acao", "alvo")
    list_filter = ("acao",)
    list_select_related = ("autor", "alvo")
    list_per_page = 20

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
