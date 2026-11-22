from django.db import models
from django.db.models import Q

from dicionario.models import Sinal
from trilha.models import Aula


class Questao(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="questoes")
    enunciado = models.CharField(max_length=500)
    sinal = models.ForeignKey(
        Sinal,
        verbose_name="vídeo de sinal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="questoes",
        help_text="Opcional: mostra o vídeo de um sinal do dicionário junto ao enunciado.",
    )
    posicao = models.PositiveIntegerField("posição", help_text="Ordem da questão no questionário.")

    class Meta:
        verbose_name = "questão"
        verbose_name_plural = "questões"
        ordering = ["aula", "posicao"]
        constraints = [
            models.UniqueConstraint(fields=["aula", "posicao"], name="questao_posicao_unica_na_aula"),
            models.CheckConstraint(condition=Q(posicao__gt=0), name="questao_posicao_positiva"),
        ]

    def __str__(self) -> str:
        return f"{self.posicao}. {self.enunciado}"


class Alternativa(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name="alternativas")
    texto = models.CharField(max_length=200)
    correta = models.BooleanField(default=False)

    class Meta:
        verbose_name = "alternativa"
        verbose_name_plural = "alternativas"
        ordering = ["id"]
        constraints = [
            # Índice único parcial: no máximo uma alternativa correta por questão (RF014).
            models.UniqueConstraint(
                fields=["questao"], condition=Q(correta=True), name="alternativa_correta_unica"
            ),
        ]

    def __str__(self) -> str:
        return self.texto
