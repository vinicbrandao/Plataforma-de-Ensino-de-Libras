from dataclasses import dataclass
from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone

from ..exceptions import CadastroDeMenorIndisponivel, CpfJaCadastrado, EmailJaCadastrado
from ..models import Usuario

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


class CadastroService:
    """Cadastro de alunos (RF001), com o bloqueio de menores até o RF002 (RF-61)."""

    @staticmethod
    def calcular_idade(nascimento: date, hoje: date) -> int:
        # Comparar (mês, dia) faz quem nasceu em 29/02 completar anos em 01/03.
        ainda_nao_fez_aniversario = (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
        return hoje.year - nascimento.year - int(ainda_nao_fez_aniversario)

    @classmethod
    def cadastrar(cls, dados: DadosCadastro) -> Usuario:
        if cls.calcular_idade(dados.data_nascimento, timezone.localdate()) < IDADE_MINIMA:
            raise CadastroDeMenorIndisponivel
        cls._verificar_duplicidade(dados)
        try:
            with transaction.atomic():
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
