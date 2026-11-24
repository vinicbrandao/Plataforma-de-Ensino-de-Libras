from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .aula import Aula


class AnotacaoAula(models.Model):
    """Anotação pessoal do aluno em uma aula (RF019, spec 0008). Texto puro (RS013)."""

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="anotacoes"
    )
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT, related_name="anotacoes")
    texto = models.CharField(max_length=2000)
    atualizada_em = models.DateTimeField("atualizada em", default=timezone.now)

    class Meta:
        verbose_name = "anotação"
        verbose_name_plural = "anotações"
        constraints = [
            models.UniqueConstraint(fields=["aluno", "aula"], name="anotacao_unica_por_aula"),
            models.CheckConstraint(condition=~Q(texto=""), name="anotacao_texto_preenchido"),
        ]

    def __str__(self) -> str:
        return f"{self.aluno} · {self.aula}"
