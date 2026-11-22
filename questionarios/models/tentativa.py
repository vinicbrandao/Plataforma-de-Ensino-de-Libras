from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from trilha.models import Aula


class Tentativa(models.Model):
    """Resultado de uma tentativa do aluno (RF009).

    Guarda só os números, para que alterar ou excluir questões não mude o histórico (RF014).
    """

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tentativas"
    )
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT, related_name="tentativas")
    acertos = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    percentual = models.PositiveSmallIntegerField()
    aprovada = models.BooleanField()
    realizada_em = models.DateTimeField("realizada em", default=timezone.now)

    class Meta:
        verbose_name = "tentativa"
        verbose_name_plural = "tentativas"
        ordering = ["-realizada_em"]
        indexes = [models.Index(fields=["aluno", "realizada_em"], name="tentativa_aluno_data_idx")]
        constraints = [
            models.CheckConstraint(condition=Q(total__gt=0), name="tentativa_total_positivo"),
            models.CheckConstraint(condition=Q(acertos__lte=F("total")), name="tentativa_acertos_validos"),
        ]

    def __str__(self) -> str:
        return f"{self.aluno} · {self.aula} · {self.acertos}/{self.total}"
