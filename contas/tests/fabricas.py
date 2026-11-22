"""Dados de teste compartilhados pelos testes do app contas."""

from datetime import date

from django.utils import timezone

from contas.models import Usuario
from contas.services import DadosCadastro

SENHA = "SenhaTeste123"
CPF_VALIDO = "529.982.247-25"
CPF_VALIDO_2 = "111.444.777-35"


def dados_cadastro(**alteracoes) -> DadosCadastro:
    valores = {
        "nome_completo": "Maria da Silva",
        "email": "maria@exemplo.com",
        "cpf": CPF_VALIDO,
        "senha": SENHA,
        "data_nascimento": date(1995, 5, 10),
        "telefone": "(11) 91234-5678",
        "deficiencia": Usuario.Deficiencia.NAO,
        "qual_deficiencia": "",
        "contato_libras": Usuario.ContatoLibras.NUNCA,
    }
    valores.update(alteracoes)
    return DadosCadastro(**valores)


def criar_aluno(**alteracoes) -> Usuario:
    dados = dados_cadastro(**alteracoes)
    return Usuario.objects.create_user(
        email=dados.email,
        password=dados.senha,
        nome_completo=dados.nome_completo,
        cpf=dados.cpf,
        data_nascimento=dados.data_nascimento,
        telefone=dados.telefone,
        deficiencia=dados.deficiencia,
        qual_deficiencia=dados.qual_deficiencia,
        contato_libras=dados.contato_libras,
        termos_aceitos_em=timezone.now(),
    )


def criar_admin(email: str = "admin@exemplo.com") -> Usuario:
    return Usuario.objects.create_superuser(
        email=email, password=SENHA, nome_completo="Administração"
    )


def dados_form_cadastro(**alteracoes) -> dict:
    valores = {
        "nome_completo": "  Maria   da Silva ",
        "email": "Maria@Exemplo.com",
        "cpf": "52998224725",
        "senha": SENHA,
        "confirmacao_senha": SENHA,
        "data_nascimento": "1995-05-10",
        "telefone": "11912345678",
        "deficiencia": "NAO",
        "qual_deficiencia": "",
        "contato_libras": "NUNCA",
        "aceite_termos": "on",
    }
    valores.update(alteracoes)
    return valores
