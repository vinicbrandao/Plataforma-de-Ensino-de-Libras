from .anotacao import AnotacaoAula
from .aula import Aula, caminho_legenda_aula, caminho_video_aula
from .avaliacao import AvaliacaoAula, AvaliacoesDaAula
from .material import MaterialComplementar, caminho_material
from .modulo import Modulo
from .progresso import ProgressoAula, ProgressoModulo

__all__ = [
    "AnotacaoAula",
    "Aula",
    "AvaliacaoAula",
    "AvaliacoesDaAula",
    "MaterialComplementar",
    "Modulo",
    "ProgressoAula",
    "ProgressoModulo",
    "caminho_legenda_aula",
    "caminho_material",
    "caminho_video_aula",
]
