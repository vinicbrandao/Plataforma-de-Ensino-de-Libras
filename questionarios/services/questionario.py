from dataclasses import dataclass

from django.db import transaction

from trilha.models import Aula
from trilha.services import ExibicaoAulaService, ProgressoService

from ..exceptions import QuestionarioSemQuestoes, RespostasIncompletas
from ..models import Alternativa, Questao, Tentativa


@dataclass(frozen=True)
class QuestionarioAberto:
    aula: Aula
    questoes: tuple[Questao, ...]
    eh_visitante: bool


@dataclass(frozen=True)
class Correcao:
    questao: Questao
    escolhida: Alternativa
    correta: Alternativa | None

    @property
    def acertou(self) -> bool:
        return self.escolhida.correta


@dataclass(frozen=True)
class Resultado:
    aula: Aula
    acertos: int
    total: int
    percentual: int
    aprovado: bool
    aula_concluida: bool
    proxima: Aula | None
    correcoes: tuple[Correcao, ...]
    eh_visitante: bool


def _eh_aluno(usuario) -> bool:
    return usuario.is_authenticated and not usuario.is_staff


class QuestionarioService:
    """Questionário da aula: correção, tentativa e conclusão (RF009, ADR 0008)."""

    @staticmethod
    def aprovado(acertos: int, total: int) -> bool:
        # 70% sem arredondamento: 7 de 10 aprova, 2 de 3 (66,7%) reprova.
        return acertos * 10 >= total * 7

    @staticmethod
    def _questoes(aula: Aula) -> tuple[Questao, ...]:
        return tuple(
            Questao.objects.filter(aula=aula)
            .select_related("sinal")
            .prefetch_related("alternativas")
            .order_by("posicao")
        )

    @classmethod
    def carregar(cls, aula_id: int, usuario) -> QuestionarioAberto:
        aula = ExibicaoAulaService.verificar_acesso(aula_id, usuario)
        return QuestionarioAberto(
            aula=aula, questoes=cls._questoes(aula), eh_visitante=not usuario.is_authenticated
        )

    @classmethod
    def corrigir(cls, aula_id: int, usuario, respostas: dict[int, int]) -> Resultado:
        aula = ExibicaoAulaService.verificar_acesso(aula_id, usuario)
        questoes = cls._questoes(aula)
        if not questoes:
            raise QuestionarioSemQuestoes
        correcoes = tuple(cls._corrigir_questao(questao, respostas.get(questao.pk)) for questao in questoes)

        total = len(correcoes)
        acertos = sum(c.acertou for c in correcoes)
        aprovado = cls.aprovado(acertos, total)
        percentual = round(100 * acertos / total)
        aula_concluida = False
        if _eh_aluno(usuario):
            with transaction.atomic():
                Tentativa.objects.create(
                    aluno=usuario, aula=aula, acertos=acertos, total=total,
                    percentual=percentual, aprovada=aprovado,
                )
                if aprovado:
                    ProgressoService.concluir(usuario, aula)
                    aula_concluida = True
        return Resultado(
            aula=aula,
            acertos=acertos,
            total=total,
            percentual=percentual,
            aprovado=aprovado,
            aula_concluida=aula_concluida,
            proxima=ExibicaoAulaService.proxima_aula(aula) if aprovado else None,
            correcoes=correcoes,
            eh_visitante=not usuario.is_authenticated,
        )

    @staticmethod
    def _corrigir_questao(questao: Questao, alternativa_id: int | None) -> Correcao:
        alternativas = {alternativa.pk: alternativa for alternativa in questao.alternativas.all()}
        if alternativa_id not in alternativas:
            raise RespostasIncompletas
        correta = next((a for a in alternativas.values() if a.correta), None)
        return Correcao(questao=questao, escolhida=alternativas[alternativa_id], correta=correta)
