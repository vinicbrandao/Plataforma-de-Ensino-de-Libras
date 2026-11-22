from ..exceptions import TermoJaCadastrado
from ..models import Sinal
from .cadastro_base import CadastroComNomeUnicoService


class SinalService(CadastroComNomeUnicoService):
    """Cadastro de sinais (RF015). O RF-55 entra em `validar_regras` na spec dos questionários."""

    modelo = Sinal
    campo = "termo"
    campo_normalizado = "termo_normalizado"
    excecao_duplicado = TermoJaCadastrado
