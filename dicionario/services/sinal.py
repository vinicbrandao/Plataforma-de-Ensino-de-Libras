from ..exceptions import SinalEmUso, TermoJaCadastrado
from ..models import Sinal
from .cadastro_base import CadastroComNomeUnicoService


class SinalService(CadastroComNomeUnicoService):
    """Cadastro de sinais (RF015)."""

    modelo = Sinal
    campo = "termo"
    campo_normalizado = "termo_normalizado"
    excecao_duplicado = TermoJaCadastrado

    @classmethod
    def validar_regras(cls, sinal: Sinal) -> None:
        cls.validar_inativacao(sinal.pk, ativo=sinal.ativo)

    @staticmethod
    def validar_inativacao(sinal_id: int | None, *, ativo: bool) -> None:
        """Um sinal usado em questão de aula publicada não pode ser inativado (RF015 ⁶).

        A consulta usa o nome reverso "questoes", sem importar o app questionarios.
        """
        if sinal_id is None or ativo:
            return
        if Sinal.objects.filter(pk=sinal_id, questoes__aula__publicada=True).exists():
            raise SinalEmUso
