"""Exceções de domínio do app questionarios."""


class ErroDeQuestionario(Exception):
    """Base das falhas previstas do app questionarios."""

    mensagem = ""


class PosicaoDeQuestaoJaCadastrada(ErroDeQuestionario):
    mensagem = "Posição já cadastrada para esta aula"


class QuantidadeDeAlternativasInvalida(ErroDeQuestionario):
    mensagem = "Cadastre de 2 a 5 alternativas"


class AlternativaCorretaInvalida(ErroDeQuestionario):
    mensagem = "Marque exatamente uma alternativa correta"


class UltimaQuestaoDeAulaPublicada(ErroDeQuestionario):
    mensagem = "A aula publicada precisa de ao menos uma questão"


class RespostasIncompletas(ErroDeQuestionario):
    mensagem = "Responda todas as questões antes de enviar"


class QuestionarioSemQuestoes(ErroDeQuestionario):
    mensagem = "Esta aula ainda não tem questões"
