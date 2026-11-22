from ..exceptions import CategoriaComSinaisAtivos, CategoriaJaCadastrada
from ..models import Categoria
from .cadastro_base import CadastroComNomeUnicoService


class CategoriaService(CadastroComNomeUnicoService):
    """Cadastro de categorias do dicionário (RF015)."""

    modelo = Categoria
    campo = "nome"
    campo_normalizado = "nome_normalizado"
    excecao_duplicado = CategoriaJaCadastrada

    @classmethod
    def validar_regras(cls, categoria: Categoria) -> None:
        cls.validar_inativacao(categoria.pk, ativa=categoria.ativa)

    @staticmethod
    def validar_inativacao(categoria_id: int | None, *, ativa: bool) -> None:
        """Uma categoria com sinais ativos não pode ser inativada (RF015 ²)."""
        if categoria_id is None or ativa:
            return
        if Categoria.objects.filter(pk=categoria_id, sinais__ativo=True).exists():
            raise CategoriaComSinaisAtivos

    @staticmethod
    def opcoes_ativas() -> list[tuple[int, str]]:
        return list(Categoria.objects.filter(ativa=True).order_by("nome").values_list("id", "nome"))
