"""Exceções de domínio do app dicionario."""


class ErroDeDicionario(Exception):
    """Base das falhas previstas do app dicionario."""


class TermoJaCadastrado(ErroDeDicionario):
    mensagem = "Termo já cadastrado"


class CategoriaJaCadastrada(ErroDeDicionario):
    mensagem = "Categoria já cadastrada"


class CategoriaComSinaisAtivos(ErroDeDicionario):
    mensagem = "Existem sinais ativos nesta categoria"
