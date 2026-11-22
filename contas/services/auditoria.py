from ..models import RegistroAuditoria, Usuario


class AuditoriaService:
    """Registra ações administrativas que o LogEntry do Admin não cobre."""

    @staticmethod
    def registrar(
        autor: Usuario, acao: RegistroAuditoria.Acao, alvo: Usuario | None = None
    ) -> RegistroAuditoria:
        return RegistroAuditoria.objects.create(autor=autor, acao=acao, alvo=alvo)
