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


class AcaoSomenteDoAluno(ErroDeTrilha):
    """Anotações e avaliações são do aluno; o administrador não grava (RF018, RF019)."""

    mensagem = "Somente alunos podem fazer isso"


class AulaNaoIniciada(ErroDeTrilha):
    """A avaliação exige a aula Em andamento ou Concluída (RF018)."""

    mensagem = "Abra a aula antes de avaliá-la"
