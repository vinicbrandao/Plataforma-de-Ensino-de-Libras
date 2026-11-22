from .aula import Aula, caminho_legenda_aula, caminho_video_aula
from .material import MaterialComplementar, caminho_material
from .modulo import Modulo
from .progresso import ProgressoAula, ProgressoModulo

__all__ = [
    "Aula",
    "MaterialComplementar",
    "Modulo",
    "ProgressoAula",
    "ProgressoModulo",
    "caminho_legenda_aula",
    "caminho_material",
    "caminho_video_aula",
]
