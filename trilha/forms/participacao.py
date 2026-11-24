from django import forms

CAMPO_OBRIGATORIO = "Campo obrigatório não preenchido"
NOTAS = [(nota, f"{nota} de 5") for nota in range(1, 6)]


class AnotacaoForm(forms.Form):
    """Anotação da aula, em texto puro (RF019, RS013)."""

    texto = forms.CharField(
        label="Minhas anotações",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": 2000}),
        error_messages={
            "required": CAMPO_OBRIGATORIO,
            "max_length": "A anotação deve ter até 2.000 caracteres",
        },
    )


class AvaliacaoForm(forms.Form):
    """Nota de 1 a 5 e comentário opcional (RF018, RS013)."""

    nota = forms.TypedChoiceField(
        label="Nota",
        choices=NOTAS,
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={"required": "Selecione uma nota de 1 a 5"},
    )
    comentario = forms.CharField(
        label="Comentário (opcional)",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        error_messages={"max_length": "O comentário deve ter até 500 caracteres"},
    )
