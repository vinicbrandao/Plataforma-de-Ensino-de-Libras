import re

from django.db.models import Q, QuerySet

from ..documentos import Cpf
from ..exceptions import UsuarioNaoEncontrado
from ..models import RegistroAuditoria, Usuario
from .auditoria import AuditoriaService

APENAS_CPF = re.compile(r"[\d.\-\s]+")


class UsuarioService:
    """Consulta e situação dos alunos na área administrativa (RF016)."""

    @staticmethod
    def alunos() -> QuerySet[Usuario]:
        return Usuario.objects.filter(is_staff=False).order_by("nome_completo")

    @classmethod
    def buscar_alunos(cls, queryset: QuerySet[Usuario], termo: str) -> QuerySet[Usuario]:
        termo = (termo or "").strip()
        if not termo:
            return queryset
        cpf = cls._cpf_valido(termo)
        if cpf:
            return queryset.filter(cpf=cpf)
        return queryset.filter(Q(nome_completo__icontains=termo) | Q(email__icontains=termo))

    @staticmethod
    def _cpf_valido(termo: str) -> str | None:
        if not APENAS_CPF.fullmatch(termo):
            return None
        try:
            return Cpf.de_texto(termo).formatado
        except ValueError:
            return None

    @classmethod
    def desativar(cls, aluno: Usuario, por: Usuario) -> None:
        cls._alterar_situacao(aluno, ativo=False, por=por, acao=RegistroAuditoria.Acao.DESATIVACAO)

    @classmethod
    def reativar(cls, aluno: Usuario, por: Usuario) -> None:
        cls._alterar_situacao(aluno, ativo=True, por=por, acao=RegistroAuditoria.Acao.REATIVACAO)

    @staticmethod
    def _alterar_situacao(
        aluno: Usuario, *, ativo: bool, por: Usuario, acao: RegistroAuditoria.Acao
    ) -> None:
        if aluno.is_staff:
            raise UsuarioNaoEncontrado
        aluno.is_active = ativo
        aluno.save(update_fields=["is_active"])
        AuditoriaService.registrar(por, acao, alvo=aluno)
