from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class Modulo(models.Model):
    titulo = models.CharField("título", max_length=100)
    descricao = models.CharField("descrição", max_length=500)
    posicao = models.PositiveIntegerField("posição", help_text="Ordem do módulo na trilha.")

    class Meta:
        verbose_name = "módulo"
        verbose_name_plural = "módulos"
        ordering = ["posicao"]
        constraints = [
            models.UniqueConstraint(Lower("titulo"), name="modulo_titulo_unico"),
            models.UniqueConstraint(fields=["posicao"], name="modulo_posicao_unica"),
            models.CheckConstraint(condition=Q(posicao__gt=0), name="modulo_posicao_positiva"),
        ]

    def __str__(self) -> str:
        return f"{self.posicao}. {self.titulo}"
