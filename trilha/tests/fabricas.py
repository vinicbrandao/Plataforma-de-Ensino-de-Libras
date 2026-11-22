"""Dados de teste do app trilha."""

from django.core.files.uploadedfile import SimpleUploadedFile

from dicionario.tests.fabricas import BYTES_MP4
from trilha.models import Aula, Modulo
from trilha.services import AulaService, ModuloService

BYTES_VTT = b"WEBVTT\n\n00:00.000 --> 00:02.000\nOl\xc3\xa1!\n"
BYTES_PDF = b"%PDF-1.7\n%conteudo de teste\n"
BYTES_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24


def video() -> SimpleUploadedFile:
    return SimpleUploadedFile("aula.mp4", BYTES_MP4, content_type="video/mp4")


def legenda() -> SimpleUploadedFile:
    return SimpleUploadedFile("aula.vtt", BYTES_VTT, content_type="text/vtt")


def criar_modulo(posicao: int = 1, titulo: str | None = None) -> Modulo:
    return ModuloService.salvar(
        Modulo(titulo=titulo or f"Módulo {posicao}", descricao="Descrição", posicao=posicao)
    )


def criar_aula(modulo: Modulo, posicao: int = 1, publicada: bool = True, titulo: str | None = None) -> Aula:
    aula = Aula(
        modulo=modulo,
        titulo=titulo or f"Aula {modulo.posicao}.{posicao}",
        descricao="Descrição da aula",
        posicao=posicao,
    )
    if publicada:
        aula.video = video()
        aula.legenda = legenda()
    AulaService.salvar(aula)
    if publicada:
        # Publica sem passar pela exigência de questão (spec 0004), para que os testes da
        # trilha não dependam do app questionarios. O banco ainda exige vídeo e legenda.
        Aula.objects.filter(pk=aula.pk).update(publicada=True)
        aula.publicada = True
    return aula
