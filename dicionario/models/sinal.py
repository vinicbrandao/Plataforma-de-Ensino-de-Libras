from uuid import uuid4

from django.contrib.postgres.indexes import GinIndex
from django.db import models

from ..validadores import VideoMp4Validator
from .categoria import Categoria


def caminho_video_sinal(instancia: "Sinal", nome_enviado: str) -> str:
    # O nome enviado é descartado: o arquivo recebe um nome gerado pelo sistema (RS012).
    return f"sinais/{uuid4().hex}.mp4"


class Sinal(models.Model):
    class ClasseGramatical(models.TextChoices):
        SUBSTANTIVO = "SUBSTANTIVO", "Substantivo"
        VERBO = "VERBO", "Verbo"
        ADJETIVO = "ADJETIVO", "Adjetivo"
        ADVERBIO = "ADVERBIO", "Advérbio"
        OUTROS = "OUTROS", "Outros"

    termo = models.CharField(
        max_length=100,
        help_text="Termos com mais de um sinal levam o sentido entre parênteses, "
        "como “manga (fruta)”.",
    )
    # Preenchido pelo SinalService; usado na unicidade e na busca sem acentos.
    termo_normalizado = models.CharField(max_length=100, unique=True, editable=False)
    classe_gramatical = models.CharField(
        "classe gramatical", max_length=20, choices=ClasseGramatical, blank=True
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, null=True, blank=True, related_name="sinais"
    )
    descricao_execucao = models.CharField("descrição da execução", max_length=500, blank=True)
    video = models.FileField(
        "vídeo do sinal",
        upload_to=caminho_video_sinal,
        validators=[VideoMp4Validator()],
        help_text="Vídeo curto em MP4, sem áudio, de até 20 MB.",
    )
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "sinal"
        verbose_name_plural = "sinais"
        ordering = ["termo"]
        indexes = [
            # Acelera a busca por parte do termo (LIKE '%texto%'), que o B-tree não atende.
            GinIndex(
                fields=["termo_normalizado"],
                name="sinal_termo_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self) -> str:
        return self.termo
