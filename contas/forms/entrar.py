from django import forms

CAMPO_OBRIGATORIO = "Campo obrigatório não preenchido"


class EntrarForm(forms.Form):
    login = forms.CharField(
        label="E-mail ou CPF",
        max_length=200,
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    senha = forms.CharField(
        label="Senha",
        strip=False,
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
