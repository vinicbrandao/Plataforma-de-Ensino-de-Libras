import re
from datetime import date

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..documentos import Cpf, Telefone
from ..models import Usuario
from ..services import DadosCadastro
from ..validadores import MENSAGEM_SENHA

CAMPO_OBRIGATORIO = "Campo obrigatório não preenchido"
NOME_VALIDO = re.compile(r"(?:[^\W\d_]|[ '’\-])+")
EMAIL_VALIDO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
IDADE_MAXIMA = 120
# Erros de senha que o RF001 resume em uma única mensagem.
CODIGOS_DA_MENSAGEM_DE_SENHA = {
    "password_too_short",
    "password_entirely_numeric",
    "senha_sem_letras_e_numeros",
}


class CadastroForm(forms.Form):
    """Valida o formato dos dados do cadastro (RF001). As regras de negócio ficam no service."""

    nome_completo = forms.CharField(label="Nome completo", max_length=120)
    email = forms.CharField(
        label="E-mail", max_length=200, widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )
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
    aceite_termos = forms.BooleanField(
        label="Li e aceito os termos de uso e a política de privacidade",
        error_messages={
            "required": "É necessário aceitar os termos de uso e a política de privacidade"
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if nome != "aceite_termos":
                campo.error_messages["required"] = CAMPO_OBRIGATORIO
        self.fields["data_nascimento"].error_messages["invalid"] = "Data de nascimento inválida"

    def clean_nome_completo(self) -> str:
        nome = re.sub(r"\s+", " ", self.cleaned_data["nome_completo"]).strip()
        if len(nome) < 3 or not NOME_VALIDO.fullmatch(nome):
            raise ValidationError("Nome inválido")
        return nome

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if not EMAIL_VALIDO.fullmatch(email):
            raise ValidationError("E-mail inválido")
        return email

    def clean_cpf(self) -> str:
        try:
            return Cpf.de_texto(self.cleaned_data["cpf"]).formatado
        except ValueError as exc:
            raise ValidationError("CPF inválido") from exc

    def clean_telefone(self) -> str:
        try:
            return Telefone.de_texto(self.cleaned_data["telefone"]).formatado
        except ValueError as exc:
            raise ValidationError("Telefone inválido") from exc

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

    def clean(self) -> dict:
        dados = super().clean()
        self._validar_qual_deficiencia(dados)
        self._validar_senha(dados)
        return dados

    def _validar_qual_deficiencia(self, dados: dict) -> None:
        if dados.get("deficiencia") != Usuario.Deficiencia.OUTRA:
            dados["qual_deficiencia"] = ""
            return
        dados["qual_deficiencia"] = re.sub(r"\s+", " ", dados.get("qual_deficiencia", "")).strip()
        if not dados["qual_deficiencia"]:
            self.add_error("qual_deficiencia", CAMPO_OBRIGATORIO)

    def _validar_senha(self, dados: dict) -> None:
        senha = dados.get("senha")
        if not senha:
            return
        if senha != dados.get("confirmacao_senha"):
            self.add_error("confirmacao_senha", "As senhas informadas não coincidem")
        usuario = Usuario(email=dados.get("email", ""), nome_completo=dados.get("nome_completo", ""))
        try:
            validate_password(senha, user=usuario)
        except ValidationError as exc:
            for mensagem in self._mensagens_de_senha(exc):
                self.add_error("senha", mensagem)

    @staticmethod
    def _mensagens_de_senha(exc: ValidationError) -> list[str]:
        mensagens = []
        for erro in exc.error_list:
            mensagem = MENSAGEM_SENHA if erro.code in CODIGOS_DA_MENSAGEM_DE_SENHA else erro.messages[0]
            if mensagem not in mensagens:
                mensagens.append(mensagem)
        return mensagens

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
