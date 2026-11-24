from dataclasses import dataclass
from datetime import date

from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from ..exceptions import (
    CpfDoResponsavelIgualAoDoAluno,
    CpfJaCadastrado,
    EmailJaCadastrado,
    ResponsavelObrigatorio,
)
from ..models import ResponsavelLegal, Usuario

IDADE_MINIMA = 18


@dataclass(frozen=True)
class DadosCadastro:
    """Dados do cadastro já validados e normalizados pelo form."""

    nome_completo: str
    email: str
    cpf: str
    senha: str
    data_nascimento: date
    telefone: str
    deficiencia: str
    qual_deficiencia: str
    contato_libras: str


@dataclass(frozen=True)
class DadosResponsavel:
    """Dados do responsável legal do aluno menor (RF002), já validados pelo form."""

    nome: str
    vinculo: str
    cpf: str
    email: str
    telefone: str


class CadastroService:
    """Cadastro de alunos (RF001) e, para menores de 18 anos, do responsável legal (RF002)."""

    @classmethod
    def eh_menor(cls, nascimento: date, hoje: date | None = None) -> bool:
        return cls.calcular_idade(nascimento, hoje or timezone.localdate()) < IDADE_MINIMA

    @staticmethod
    def calcular_idade(nascimento: date, hoje: date) -> int:
        # Comparar (mês, dia) faz quem nasceu em 29/02 completar anos em 01/03.
        ainda_nao_fez_aniversario = (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
        return hoje.year - nascimento.year - int(ainda_nao_fez_aniversario)

    @classmethod
    def cadastrar(cls, dados: DadosCadastro, responsavel: DadosResponsavel | None = None) -> Usuario:
        menor = cls.eh_menor(dados.data_nascimento)
        if menor and responsavel is None:
            raise ResponsavelObrigatorio
        if menor and responsavel.cpf == dados.cpf:
            raise CpfDoResponsavelIgualAoDoAluno
        cls._verificar_duplicidade(dados)
        try:
            with transaction.atomic():
                usuario = Usuario.objects.create_user(
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
                if menor:
                    # Aluno e responsável são gravados juntos (RF002).
                    ResponsavelLegal.objects.create(
                        aluno=usuario, termo_aceito_em=timezone.now(), **vars(responsavel)
                    )
                    transaction.on_commit(lambda: cls._avisar_responsavel(usuario, responsavel))
                return usuario
        except IntegrityError:
            # Outro cadastro com o mesmo e-mail ou CPF pode ter sido gravado entre a
            # verificação e o insert. A nova verificação identifica qual dado se repetiu.
            cls._verificar_duplicidade(dados)
            raise

    @staticmethod
    def _verificar_duplicidade(dados: DadosCadastro) -> None:
        if Usuario.objects.filter(email__iexact=dados.email).exists():
            raise EmailJaCadastrado
        if Usuario.objects.filter(cpf=dados.cpf).exists():
            raise CpfJaCadastrado

    @staticmethod
    def _avisar_responsavel(aluno: Usuario, responsavel: DadosResponsavel) -> None:
        # Sem dados sensíveis, como a deficiência (RF002, RS006).
        send_mail(
            "Cadastro na Plataforma de Ensino de Libras",
            f"Olá, {responsavel.nome}.\n\n"
            f"{aluno.nome_completo} se cadastrou na Plataforma de Ensino de Libras em "
            f"{timezone.localdate():%d/%m/%Y}, com a sua autorização como responsável legal.",
            None,
            [responsavel.email],
        )
