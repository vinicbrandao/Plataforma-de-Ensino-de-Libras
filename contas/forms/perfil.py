from django import forms

from core.validadores import ImagemPerfilValidator

from ..models import VinculoResponsavel
from ..services import DadosPerfil, DadosResponsavel
from .dados_pessoais import (
    CAMPO_OBRIGATORIO,
    DadosPessoaisForm,
    normalizar_cpf,
    normalizar_email,
    normalizar_nome,
    normalizar_telefone,
)
from .senha import ValidacaoDeSenhaMixin


class PerfilForm(DadosPessoaisForm):
    """Dados que o aluno altera no perfil (RF005). CPF e data de nascimento não entram."""

    receber_lembretes = forms.BooleanField(label="Receber lembretes de estudo por e-mail", required=False)

    def dados(self) -> DadosPerfil:
        d = self.cleaned_data
        return DadosPerfil(
            nome_completo=d["nome_completo"],
            email=d["email"],
            telefone=d["telefone"],
            deficiencia=d["deficiencia"],
            qual_deficiencia=d["qual_deficiencia"],
            contato_libras=d["contato_libras"],
            receber_lembretes=d["receber_lembretes"],
        )


class FotoForm(forms.Form):
    """Foto de perfil JPG ou PNG de até 2 MB, validada pelo tipo real (RF005, RS012)."""

    foto = forms.FileField(
        label="Foto de perfil",
        validators=[ImagemPerfilValidator()],
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png"}),
    )


class TrocaSenhaForm(ValidacaoDeSenhaMixin, forms.Form):
    """Troca de senha com a senha atual e as regras da nova senha do RF004 (RF005, RS007)."""

    senha_atual = forms.CharField(
        label="Senha atual",
        strip=False,
        error_messages={"required": CAMPO_OBRIGATORIO},
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
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


class ResponsavelForm(forms.Form):
    """Dados do responsável que o aluno menor altera no perfil (RF002, RF005)."""

    nome = forms.CharField(label="Nome do responsável", max_length=120)
    vinculo = forms.ChoiceField(label="Vínculo", choices=VinculoResponsavel.choices, widget=forms.RadioSelect)
    cpf = forms.CharField(label="CPF do responsável", max_length=14)
    email = forms.CharField(label="E-mail do responsável", max_length=200, widget=forms.EmailInput())
    telefone = forms.CharField(label="Telefone do responsável", max_length=15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.error_messages["required"] = CAMPO_OBRIGATORIO

    def clean_nome(self) -> str:
        return normalizar_nome(self.cleaned_data["nome"])

    def clean_cpf(self) -> str:
        return normalizar_cpf(self.cleaned_data["cpf"], "CPF do responsável inválido")

    def clean_email(self) -> str:
        return normalizar_email(self.cleaned_data["email"])

    def clean_telefone(self) -> str:
        return normalizar_telefone(self.cleaned_data["telefone"])

    def dados(self) -> DadosResponsavel:
        return DadosResponsavel(**self.cleaned_data)
