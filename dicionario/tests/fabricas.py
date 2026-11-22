"""Dados de teste do app dicionario."""

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from dicionario.models import Categoria, Sinal
from dicionario.services import CategoriaService, SinalService

# Cabeçalho mínimo de um MP4: caixa "ftyp" com a marca "isom".
BYTES_MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2" + b"\x00" * 32


def video_mp4(nome: str = "sinal.mp4") -> SimpleUploadedFile:
    return SimpleUploadedFile(nome, BYTES_MP4, content_type="video/mp4")


def criar_categoria(nome: str = "Família", ativa: bool = True) -> Categoria:
    return CategoriaService.salvar(Categoria(nome=nome, ativa=ativa))


def criar_sinal(termo: str = "Mãe", categoria: Categoria | None = None, ativo: bool = True) -> Sinal:
    return SinalService.salvar(
        Sinal(termo=termo, categoria=categoria, ativo=ativo, video=video_mp4())
    )


class MidiaTemporariaMixin:
    """Grava os arquivos enviados em uma pasta temporária, apagada ao final da classe."""

    @classmethod
    def setUpClass(cls):
        cls._pasta_midia = tempfile.mkdtemp()
        cls._override_midia = override_settings(MEDIA_ROOT=cls._pasta_midia)
        cls._override_midia.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override_midia.disable()
        shutil.rmtree(cls._pasta_midia, ignore_errors=True)
