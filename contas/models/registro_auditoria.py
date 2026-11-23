from django.conf import settings
from django.db import models


class AcaoAuditoria(models.TextChoices):
    LOGIN_ADMIN = "LOGIN_ADMIN", "Login de administrador"
    LOGOUT_ADMIN = "LOGOUT_ADMIN", "Logout de administrador"
    CONSULTA_ALUNO = "CONSULTA_ALUNO", "Consulta ao detalhe de aluno"
    DESATIVACAO = "DESATIVACAO", "Desativação de aluno"
    REATIVACAO = "REATIVACAO", "Reativação de aluno"


class RegistroAuditoria(models.Model):
    """Ações administrativas que o LogEntry do Admin não registra (RS004, RS009)."""

    # No módulo porque a class Meta não enxerga os atributos da classe.
    Acao = AcaoAuditoria

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="registros_feitos"
    )
    acao = models.CharField("ação", max_length=20, choices=Acao)
    alvo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registros_recebidos",
    )
    criado_em = models.DateTimeField("data e hora", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"
        ordering = ["-criado_em"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(acao__in=AcaoAuditoria.values),
                name="contas_registroauditoria_acao_valido",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_acao_display()} por {self.autor}"
