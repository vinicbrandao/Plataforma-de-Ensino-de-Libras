from django.db import transaction

from ..exceptions import (
    AlternativaCorretaInvalida,
    PosicaoDeQuestaoJaCadastrada,
    QuantidadeDeAlternativasInvalida,
    UltimaQuestaoDeAulaPublicada,
)
from ..models import Questao

MINIMO_DE_ALTERNATIVAS = 2
MAXIMO_DE_ALTERNATIVAS = 5


class QuestaoService:
    """Cadastro de questões pela área administrativa (RF014)."""

    @staticmethod
    def validar_posicao(aula_id: int, posicao: int, ignorar_pk: int | None = None) -> None:
        if Questao.objects.filter(aula_id=aula_id, posicao=posicao).exclude(pk=ignorar_pk).exists():
            raise PosicaoDeQuestaoJaCadastrada

    @staticmethod
    def validar_alternativas(corretas: list[bool]) -> None:
        """Recebe uma entrada por alternativa: verdadeira quando ela é a correta."""
        if not MINIMO_DE_ALTERNATIVAS <= len(corretas) <= MAXIMO_DE_ALTERNATIVAS:
            raise QuantidadeDeAlternativasInvalida
        if sum(corretas) != 1:
            raise AlternativaCorretaInvalida

    @staticmethod
    def validar_exclusao(questao: Questao) -> None:
        aula = questao.aula
        outras = Questao.objects.filter(aula=aula).exclude(pk=questao.pk)
        if aula.publicada and not outras.exists():
            raise UltimaQuestaoDeAulaPublicada

    @classmethod
    def salvar(cls, questao: Questao) -> Questao:
        cls.validar_posicao(questao.aula_id, questao.posicao, ignorar_pk=questao.pk)
        questao.save()
        return questao

    @classmethod
    def excluir(cls, questao: Questao) -> None:
        with transaction.atomic():
            cls.validar_exclusao(questao)
            questao.delete()
