from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

MEGABYTE = 1024 * 1024


@deconstructible
class VideoMp4Validator:
    """Confere o tamanho e a assinatura real de um MP4, sem confiar na extensão (RS012)."""

    def __init__(self, tamanho_maximo: int = 20 * MEGABYTE):
        self.tamanho_maximo = tamanho_maximo

    @property
    def mensagem(self) -> str:
        return (
            f"Arquivo inválido: envie um vídeo MP4 de até {self.tamanho_maximo // MEGABYTE} MB"
        )

    def __call__(self, arquivo) -> None:
        if arquivo.size > self.tamanho_maximo or not self._tem_assinatura_mp4(arquivo):
            raise ValidationError(self.mensagem, code="video_invalido")

    @staticmethod
    def _tem_assinatura_mp4(arquivo) -> bool:
        posicao = arquivo.tell()
        arquivo.seek(0)
        cabecalho = arquivo.read(12)
        arquivo.seek(posicao)
        # Todo MP4 começa com uma caixa "ftyp": 4 bytes de tamanho seguidos de b"ftyp".
        return cabecalho[4:8] == b"ftyp"

    def __eq__(self, outro) -> bool:
        return isinstance(outro, VideoMp4Validator) and outro.tamanho_maximo == self.tamanho_maximo
