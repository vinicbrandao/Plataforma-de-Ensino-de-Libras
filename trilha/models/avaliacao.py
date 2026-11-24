from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .aula import Aula


class AvaliacaoAula(models.Model):
    """Nota de 1 a 5 e comentário opcional do aluno sobre uma aula (RF018, spec 0009)."""

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="avaliacoes"
    )
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT, related_name="avaliacoes")
    nota = models.PositiveSmallIntegerField()
    comentario = models.CharField("comentário", max_length=500, blank=True)
    avaliada_em = models.DateTimeField("avaliada em", default=timezone.now)

    class Meta:
        verbose_name = "avaliação de aula"
        verbose_name_plural = "avaliações de aulas"
        constraints = [
            models.UniqueConstraint(fields=["aluno", "aula"], name="avaliacao_unica_por_aula"),
            models.CheckConstraint(condition=Q(nota__gte=1, nota__lte=5), name="avaliacao_nota_valida"),
        ]

    def __str__(self) -> str:
        return f"{self.aula} · {self.nota} de 5"


class AvaliacoesDaAula(Aula):
    """Aula vista pelas avaliações, para a consulta do administrador (RF018). Sem tabela própria."""

    class Meta:
        proxy = True
        verbose_name = "avaliações da aula"
        verbose_name_plural = "avaliações das aulas"
