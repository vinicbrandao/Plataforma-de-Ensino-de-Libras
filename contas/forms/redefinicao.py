from django import forms

from .senha import ValidacaoDeSenhaMixin

CAMPO_OBRIGATORIO = "Campo obrigatório não preenchido"


class SolicitarRedefinicaoForm(forms.Form):
    """E-mail para receber o link de redefinição (RF004)."""

    email = forms.CharField(
        label="E-mail",
        max_length=200,
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )


class NovaSenhaForm(ValidacaoDeSenhaMixin, forms.Form):
    """Nova senha com as regras do RF001 (RF004)."""

    nova_senha = forms.CharField(
        label="Nova senha",
        strip=False,
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirmacao = forms.CharField(
        label="Confirmação da nova senha",
        strip=False,
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario

    def clean(self) -> dict:
        dados = super().clean()
        self.validar_senha_nova(dados, "nova_senha", "confirmacao", self.usuario)
        return dados
