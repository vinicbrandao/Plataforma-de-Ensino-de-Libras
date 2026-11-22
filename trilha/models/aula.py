from uuid import uuid4

from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from core.validadores import MEGABYTE, LegendaVttValidator, VideoMp4Validator

from .modulo import Modulo


def caminho_video_aula(instancia: "Aula", nome_enviado: str) -> str:
    return f"aulas/videos/{uuid4().hex}.mp4"


def caminho_legenda_aula(instancia: "Aula", nome_enviado: str) -> str:
    return f"aulas/legendas/{uuid4().hex}.vtt"


class Aula(models.Model):
    modulo = models.ForeignKey(
        Modulo, verbose_name="módulo", on_delete=models.PROTECT, related_name="aulas"
    )
    titulo = models.CharField("título", max_length=100)
    descricao = models.CharField("descrição", max_length=500)
    posicao = models.PositiveIntegerField("posição", help_text="Ordem da aula no módulo.")
    video = models.FileField(
        "vídeo",
        upload_to=caminho_video_aula,
        blank=True,
        validators=[VideoMp4Validator(200 * MEGABYTE)],
        help_text="MP4 de até 200 MB. Obrigatório para publicar.",
    )
    legenda = models.FileField(
        "legenda em português",
        upload_to=caminho_legenda_aula,
        blank=True,
        validators=[LegendaVttValidator()],
        help_text="Arquivo WebVTT (.vtt). Obrigatório para publicar.",
    )
    texto_apoio = models.CharField("texto de apoio", max_length=2000, blank=True)
    publicada = models.BooleanField("publicada", default=False)

    class Meta:
        verbose_name = "aula"
        verbose_name_plural = "aulas"
        ordering = ["modulo__posicao", "posicao"]
        constraints = [
            models.UniqueConstraint(F("modulo"), Lower("titulo"), name="aula_titulo_unico_no_modulo"),
            models.UniqueConstraint(fields=["modulo", "posicao"], name="aula_posicao_unica_no_modulo"),
            models.CheckConstraint(condition=Q(posicao__gt=0), name="aula_posicao_positiva"),
            models.CheckConstraint(
                condition=Q(publicada=False) | (~Q(video="") & ~Q(legenda="")),
                name="aula_publicada_completa",
            ),
        ]

    def __str__(self) -> str:
        return self.titulo
