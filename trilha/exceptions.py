"""Exceções de domínio do app trilha."""


class ErroDeTrilha(Exception):
    """Base das falhas previstas do app trilha."""


class TituloJaCadastrado(ErroDeTrilha):
    mensagem = "Título já cadastrado"


class PosicaoJaCadastrada(ErroDeTrilha):
    mensagem = "Posição já cadastrada"


class AulaIncompletaParaPublicar(ErroDeTrilha):
    mensagem = "A aula precisa de vídeo, legenda e questões para ser publicada"


class AulaNaoEncontrada(ErroDeTrilha):
    pass


class AulaRestritaAVisitante(ErroDeTrilha):
    """O visitante só abre a primeira aula publicada da trilha (RF006)."""
