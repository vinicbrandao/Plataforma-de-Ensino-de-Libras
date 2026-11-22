"""Dados de teste do app questionarios."""

from questionarios.models import Alternativa, Questao
from trilha.models import Aula


def criar_questao(
    aula: Aula, posicao: int = 1, corretas: tuple[bool, ...] = (True, False, False), sinal=None
) -> Questao:
    questao = Questao.objects.create(
        aula=aula, enunciado=f"Questão {posicao}", posicao=posicao, sinal=sinal
    )
    for indice, correta in enumerate(corretas, start=1):
        Alternativa.objects.create(questao=questao, texto=f"Q{posicao} opção {indice}", correta=correta)
    return questao


def respostas(questoes: list[Questao], acertos: int) -> dict[int, int]:
    """Responde certo as `acertos` primeiras questões e errado as demais."""
    escolhidas = {}
    for indice, questao in enumerate(questoes):
        acertar = indice < acertos
        alternativa = questao.alternativas.filter(correta=acertar).first()
        escolhidas[questao.pk] = alternativa.pk
    return escolhidas
