from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import Usuario, VinculoResponsavel
from ..services import CadastroService, DadosCadastro, DadosResponsavel
from ..validadores import MENSAGEM_SENHA
from .dados_pessoais import (
    CAMPO_OBRIGATORIO,
    DadosPessoaisForm,
    normalizar_cpf,
    normalizar_email,
    normalizar_nome,
    normalizar_telefone,
)
from .senha import ValidacaoDeSenhaMixin

IDADE_MAXIMA = 120
CAMPOS_DO_RESPONSAVEL = (
    "responsavel_nome",
    "responsavel_vinculo",
    "responsavel_cpf",
    "responsavel_email",
    "responsavel_telefone",
)
AUTORIZACAO_OBRIGATORIA = "É necessário confirmar a autorização do responsável"


class CadastroForm(ValidacaoDeSenhaMixin, DadosPessoaisForm):
    """Valida o formato dos dados do cadastro (RF001). As regras de negócio ficam no service."""

    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        help_text="Com ou sem pontuação.",
        widget=forms.TextInput(attrs={"inputmode": "numeric"}),
    )
    senha = forms.CharField(
        label="Senha",
        strip=False,
        help_text=MENSAGEM_SENHA + ".",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirmacao_senha = forms.CharField(
        label="Confirmação de senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    data_nascimento = forms.DateField(
        label="Data de nascimento",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
    )
    aceite_termos = forms.BooleanField(
        label="Li e aceito os termos de uso e a política de privacidade",
        error_messages={
            "required": "É necessário aceitar os termos de uso e a política de privacidade"
        },
    )

    # Responsável legal (RF002): opcionais no form; o clean exige para menores de 18 anos.
    responsavel_nome = forms.CharField(label="Nome do responsável", max_length=120, required=False)
    responsavel_vinculo = forms.ChoiceField(
        label="Vínculo", choices=VinculoResponsavel.choices, widget=forms.RadioSelect, required=False
    )
    responsavel_cpf = forms.CharField(
        label="CPF do responsável",
        max_length=14,
        required=False,
        widget=forms.TextInput(attrs={"inputmode": "numeric"}),
    )
    responsavel_email = forms.CharField(
        label="E-mail do responsável", max_length=200, required=False, widget=forms.EmailInput()
    )
    responsavel_telefone = forms.CharField(
        label="Telefone do responsável",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"inputmode": "tel"}),
    )
    aceite_responsavel = forms.BooleanField(
        label="Confirmo que o responsável legal autorizou o cadastro e leu o termo de autorização e consentimento",
        required=False,
    )

    campos_com_mensagem_propria = ("aceite_termos",)
    field_order = [
        "nome_completo",
        "email",
        "cpf",
        "senha",
        "confirmacao_senha",
        "data_nascimento",
        "telefone",
        "deficiencia",
        "qual_deficiencia",
        "contato_libras",
        *CAMPOS_DO_RESPONSAVEL,
        "aceite_responsavel",
        "aceite_termos",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_nascimento"].error_messages["invalid"] = "Data de nascimento inválida"

    def clean_cpf(self) -> str:
        return normalizar_cpf(self.cleaned_data["cpf"])

    def clean_data_nascimento(self) -> date:
        nascimento = self.cleaned_data["data_nascimento"]
        hoje = timezone.localdate()
        if nascimento > hoje or nascimento < self._data_limite(hoje):
            raise ValidationError("Data de nascimento inválida")
        return nascimento

    @staticmethod
    def _data_limite(hoje: date) -> date:
        try:
            return hoje.replace(year=hoje.year - IDADE_MAXIMA)
        except ValueError:  # 29/02 em ano sem esse dia.
            return hoje.replace(year=hoje.year - IDADE_MAXIMA, day=28)

    # Os campos do responsável são opcionais no form: vazios passam, preenchidos seguem o RF001.
    def clean_responsavel_nome(self) -> str:
        texto = self.cleaned_data["responsavel_nome"]
        return normalizar_nome(texto) if texto.strip() else ""

    def clean_responsavel_cpf(self) -> str:
        texto = self.cleaned_data["responsavel_cpf"]
        return normalizar_cpf(texto, "CPF do responsável inválido") if texto.strip() else ""

    def clean_responsavel_email(self) -> str:
        texto = self.cleaned_data["responsavel_email"]
        return normalizar_email(texto) if texto.strip() else ""

    def clean_responsavel_telefone(self) -> str:
        texto = self.cleaned_data["responsavel_telefone"]
        return normalizar_telefone(texto) if texto.strip() else ""

    def clean(self) -> dict:
        dados = super().clean()
        usuario = Usuario(email=dados.get("email", ""), nome_completo=dados.get("nome_completo", ""))
        self.validar_senha_nova(dados, "senha", "confirmacao_senha", usuario)
        self._validar_responsavel(dados)
        return dados

    def eh_menor(self) -> bool:
        nascimento = self.cleaned_data.get("data_nascimento")
        return nascimento is not None and CadastroService.eh_menor(nascimento)

    def _validar_responsavel(self, dados: dict) -> None:
        if not self.eh_menor():
            # Para 18 anos ou mais, os dados do responsável são descartados (RF002).
            for campo in (*CAMPOS_DO_RESPONSAVEL, "aceite_responsavel"):
                dados[campo] = False if campo == "aceite_responsavel" else ""
            return
        for campo in CAMPOS_DO_RESPONSAVEL:
            if not dados.get(campo) and campo not in self.errors:
                self.add_error(campo, CAMPO_OBRIGATORIO)
        if not dados.get("aceite_responsavel"):
            self.add_error("aceite_responsavel", AUTORIZACAO_OBRIGATORIA)

    def responsavel(self) -> DadosResponsavel | None:
        if not self.eh_menor():
            return None
        d = self.cleaned_data
        return DadosResponsavel(
            nome=d["responsavel_nome"],
            vinculo=d["responsavel_vinculo"],
            cpf=d["responsavel_cpf"],
            email=d["responsavel_email"],
            telefone=d["responsavel_telefone"],
        )

    def dados(self) -> DadosCadastro:
        d = self.cleaned_data
        return DadosCadastro(
            nome_completo=d["nome_completo"],
            email=d["email"],
            cpf=d["cpf"],
            senha=d["senha"],
            data_nascimento=d["data_nascimento"],
            telefone=d["telefone"],
            deficiencia=d["deficiencia"],
            qual_deficiencia=d["qual_deficiencia"],
            contato_libras=d["contato_libras"],
        )
