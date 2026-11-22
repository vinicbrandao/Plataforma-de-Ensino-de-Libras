from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """Ações administrativas que o LogEntry do Admin não registra (RS004, RS009)."""

    class Acao(models.TextChoices):
        LOGIN_ADMIN = "LOGIN_ADMIN", "Login de administrador"
        LOGOUT_ADMIN = "LOGOUT_ADMIN", "Logout de administrador"
        CONSULTA_ALUNO = "CONSULTA_ALUNO", "Consulta ao detalhe de aluno"
        DESATIVACAO = "DESATIVACAO", "Desativação de aluno"
        REATIVACAO = "REATIVACAO", "Reativação de aluno"

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

    def __str__(self) -> str:
        return f"{self.get_acao_display()} por {self.autor}"
