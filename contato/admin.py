from django import forms
from django.contrib import admin

from .exceptions import ErroDeContato
from .models import MensagemContato
from .services import MensagemService


class MensagemContatoAdminForm(forms.ModelForm):
    """O administrador altera só a situação e a resposta, com as regras do service (RF020)."""

    class Meta:
        model = MensagemContato
        fields = ["situacao", "resposta"]
        widgets = {"resposta": forms.Textarea(attrs={"rows": 4, "maxlength": 1000})}

    def clean(self):
        dados = super().clean()
        situacao_atual = self.instance.situacao
        try:
            MensagemService.validar_atualizacao(
                situacao_atual, dados.get("situacao", situacao_atual), dados.get("resposta", "")
            )
        except ErroDeContato as exc:
            self.add_error(None, exc.mensagem)
        return dados


@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    """Fila do Fale conosco. Mostra nome e e-mail do aluno, nunca CPF nem deficiência (RNF006)."""

    form = MensagemContatoAdminForm
    list_display = ("enviada_em", "nome_do_aluno", "email_do_aluno", "assunto", "aula", "situacao")
    list_filter = ("assunto", "situacao")
    list_per_page = 20
    fields = (
        "nome_do_aluno",
        "email_do_aluno",
        "assunto",
        "aula",
        "mensagem",
        "enviada_em",
        "situacao",
        "resposta",
        "resolvida_em",
    )
    readonly_fields = (
        "nome_do_aluno",
        "email_do_aluno",
        "assunto",
        "aula",
        "mensagem",
        "enviada_em",
        "resolvida_em",
    )

    def get_queryset(self, request):
        return MensagemService.fila()

    def get_ordering(self, request):
        # A ordem da fila (não resolvidas e mais antigas primeiro) vem do service.
        return ()

    @admin.display(description="aluno", ordering="aluno__nome_completo")
    def nome_do_aluno(self, mensagem):
        return mensagem.aluno.nome_completo

    @admin.display(description="e-mail", ordering="aluno__email")
    def email_do_aluno(self, mensagem):
        return mensagem.aluno.email

    def save_model(self, request, obj, form, change):
        situacao_anterior = MensagemContato.objects.values_list("situacao", flat=True).get(pk=obj.pk)
        MensagemService.atualizar(obj, situacao_anterior)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
