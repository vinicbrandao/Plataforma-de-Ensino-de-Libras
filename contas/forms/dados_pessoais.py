import re

from django import forms
from django.core.exceptions import ValidationError

from ..documentos import Cpf, Telefone
from ..models import Usuario

CAMPO_OBRIGATORIO = "Campo obrigatório não preenchido"
NOME_VALIDO = re.compile(r"(?:[^\W\d_]|[ '’\-])+")
EMAIL_VALIDO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


# Regras de formato do RF001, usadas pelo aluno e pelo responsável legal (RF002).
def normalizar_nome(texto: str) -> str:
    nome = re.sub(r"\s+", " ", texto or "").strip()
    if len(nome) < 3 or not NOME_VALIDO.fullmatch(nome):
        raise ValidationError("Nome inválido")
    return nome


def normalizar_email(texto: str) -> str:
    email = (texto or "").strip().lower()
    if not EMAIL_VALIDO.fullmatch(email):
        raise ValidationError("E-mail inválido")
    return email


def normalizar_telefone(texto: str) -> str:
    try:
        return Telefone.de_texto(texto).formatado
    except ValueError as exc:
        raise ValidationError("Telefone inválido") from exc


def normalizar_cpf(texto: str, mensagem: str = "CPF inválido") -> str:
    try:
        return Cpf.de_texto(texto).formatado
    except ValueError as exc:
        raise ValidationError(mensagem) from exc


class DadosPessoaisForm(forms.Form):
    """Campos que o aluno informa no cadastro (RF001) e altera no perfil (RF005), com as mesmas regras."""

    nome_completo = forms.CharField(label="Nome completo", max_length=120)
    email = forms.CharField(
        label="E-mail", max_length=200, widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )
    telefone = forms.CharField(
        label="Telefone celular",
        max_length=15,
        help_text="Com DDD, por exemplo (11) 91234-5678.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
    )
    deficiencia = forms.ChoiceField(
        label="Possui deficiência?",
        choices=Usuario.Deficiencia.choices,
        widget=forms.RadioSelect,
    )
    qual_deficiencia = forms.CharField(
        label="Qual deficiência?",
        max_length=120,
        required=False,
        help_text="Preencha somente se escolheu “Sim, outra”.",
    )
    contato_libras = forms.ChoiceField(
        label="Já teve contato com Libras?",
        choices=Usuario.ContatoLibras.choices,
        widget=forms.RadioSelect,
    )

    # Campos com mensagem de obrigatório própria, que o __init__ não sobrescreve.
    campos_com_mensagem_propria: tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if nome not in self.campos_com_mensagem_propria:
                campo.error_messages["required"] = CAMPO_OBRIGATORIO

    def clean_nome_completo(self) -> str:
        return normalizar_nome(self.cleaned_data["nome_completo"])

    def clean_email(self) -> str:
        return normalizar_email(self.cleaned_data["email"])

    def clean_telefone(self) -> str:
        return normalizar_telefone(self.cleaned_data["telefone"])

    def clean(self) -> dict:
        dados = super().clean()
        self._validar_qual_deficiencia(dados)
        return dados

    def _validar_qual_deficiencia(self, dados: dict) -> None:
        if dados.get("deficiencia") != Usuario.Deficiencia.OUTRA:
            dados["qual_deficiencia"] = ""
            return
        dados["qual_deficiencia"] = re.sub(r"\s+", " ", dados.get("qual_deficiencia", "")).strip()
        if not dados["qual_deficiencia"]:
            self.add_error("qual_deficiencia", CAMPO_OBRIGATORIO)
