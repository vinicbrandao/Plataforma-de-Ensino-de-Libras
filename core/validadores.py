"""Validadores de arquivos enviados, compartilhados pelos apps (RS012).

Conferem o tamanho e a assinatura real do conteúdo, sem confiar na extensão.
Não contêm regra de negócio.
"""

from abc import ABC, abstractmethod

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

MEGABYTE = 1024 * 1024
BYTES_LIDOS = 16


class ArquivoValidator(ABC):
    """Base abstrata: as subclasses informam a descrição e implementam `conteudo_valido`."""

    descricao = "um arquivo"
    tamanho_padrao = 10 * MEGABYTE

    def __init__(self, tamanho_maximo: int | None = None):
        self.tamanho_maximo = tamanho_maximo or self.tamanho_padrao

    @property
    def mensagem(self) -> str:
        return (
            f"Arquivo inválido: envie {self.descricao} de até "
            f"{self.tamanho_maximo // MEGABYTE} MB"
        )

    @abstractmethod
    def conteudo_valido(self, cabecalho: bytes) -> bool:
        """Diz se os primeiros bytes do arquivo são do tipo esperado."""

    def __call__(self, arquivo) -> None:
        if arquivo.size > self.tamanho_maximo or not self.conteudo_valido(self._ler_cabecalho(arquivo)):
            raise ValidationError(self.mensagem, code="arquivo_invalido")

    @staticmethod
    def _ler_cabecalho(arquivo) -> bytes:
        posicao = arquivo.tell()
        arquivo.seek(0)
        cabecalho = arquivo.read(BYTES_LIDOS)
        arquivo.seek(posicao)
        return cabecalho

    def __eq__(self, outro) -> bool:
        return type(outro) is type(self) and outro.tamanho_maximo == self.tamanho_maximo


@deconstructible
class VideoMp4Validator(ArquivoValidator):
    descricao = "um vídeo MP4"
    tamanho_padrao = 50 * MEGABYTE

    def conteudo_valido(self, cabecalho: bytes) -> bool:
        # Todo MP4 começa com uma caixa "ftyp": 4 bytes de tamanho seguidos de b"ftyp".
        return cabecalho[4:8] == b"ftyp"


@deconstructible
class LegendaVttValidator(ArquivoValidator):
    descricao = "uma legenda WebVTT (.vtt)"
    tamanho_padrao = 1 * MEGABYTE

    def conteudo_valido(self, cabecalho: bytes) -> bool:
        return cabecalho.removeprefix(b"\xef\xbb\xbf").startswith(b"WEBVTT")


@deconstructible
class MaterialValidator(ArquivoValidator):
    descricao = "um PDF, JPG ou PNG"
    tamanho_padrao = 10 * MEGABYTE
    ASSINATURAS = {b"%PDF": "pdf", b"\xff\xd8\xff": "jpg", b"\x89PNG": "png"}

    @classmethod
    def extensao(cls, cabecalho: bytes) -> str | None:
        for assinatura, extensao in cls.ASSINATURAS.items():
            if cabecalho.startswith(assinatura):
                return extensao
        return None

    def conteudo_valido(self, cabecalho: bytes) -> bool:
        return self.extensao(cabecalho) is not None


@deconstructible
class ImagemPerfilValidator(ArquivoValidator):
    """Foto de perfil JPG ou PNG de até 2 MB (RF005)."""

    descricao = "uma imagem JPG ou PNG"
    tamanho_padrao = 2 * MEGABYTE
    ASSINATURAS = (b"\xff\xd8\xff", b"\x89PNG")

    @property
    def mensagem(self) -> str:
        return f"Arquivo inválido. Envie uma imagem JPG ou PNG de até {self.tamanho_maximo // MEGABYTE} MB"

    def conteudo_valido(self, cabecalho: bytes) -> bool:
        return cabecalho.startswith(self.ASSINATURAS)
