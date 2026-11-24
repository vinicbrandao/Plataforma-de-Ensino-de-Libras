from django.conf import settings
from django.db import models
from django.utils import timezone

from .sinal import Sinal


class Favorito(models.Model):
    """Sinal marcado como favorito pelo aluno (RF017, spec 0007)."""

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="favoritos"
    )
    # Excluir o sinal remove os favoritos dele (RF017).
    sinal = models.ForeignKey(Sinal, on_delete=models.CASCADE, related_name="favoritos")
    criado_em = models.DateTimeField("incluído em", default=timezone.now)

    class Meta:
        verbose_name = "favorito"
        verbose_name_plural = "favoritos"
        ordering = ["sinal__termo"]
        constraints = [
            models.UniqueConstraint(fields=["aluno", "sinal"], name="favorito_unico_por_aluno"),
        ]

    def __str__(self) -> str:
        return f"{self.aluno} · {self.sinal}"
