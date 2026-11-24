from django import forms

from ..models import AssuntoMensagem

CAMPO_OBRIGATORIO = "Campo obrigatório não preenchido"
TAMANHO_DA_MENSAGEM = "A mensagem deve ter entre 10 e 1.000 caracteres"


class MensagemContatoForm(forms.Form):
    """Mensagem do aluno à equipe, em texto puro (RF020, RS013). As aulas vêm do service."""

    assunto = forms.ChoiceField(
        label="Assunto",
        choices=[("", "Selecione"), *AssuntoMensagem.choices],
        error_messages={"required": CAMPO_OBRIGATORIO},
    )
    aula = forms.TypedChoiceField(
        label="Aula relacionada (opcional)", required=False, coerce=int, empty_value=None
    )
    mensagem = forms.CharField(
        label="Mensagem",
        min_length=10,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 6, "maxlength": 1000}),
        error_messages={
            "required": CAMPO_OBRIGATORIO,
            "min_length": TAMANHO_DA_MENSAGEM,
            "max_length": TAMANHO_DA_MENSAGEM,
        },
    )

    def __init__(self, *args, aulas=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aula"].choices = [("", "Nenhuma"), *(aulas or [])]
