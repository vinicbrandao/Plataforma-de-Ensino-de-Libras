"""Exceções de domínio do app contato."""


class ErroDeContato(Exception):
    """Base das falhas previstas do app contato."""

    mensagem = ""


class LimiteDiarioAtingido(ErroDeContato):
    mensagem = "Limite de 5 mensagens por dia atingido. Tente novamente amanhã"


class RespostaObrigatoria(ErroDeContato):
    mensagem = "Informe a resposta para marcar como resolvida"


class MensagemJaResolvida(ErroDeContato):
    mensagem = "Uma mensagem resolvida não volta a outra situação"
