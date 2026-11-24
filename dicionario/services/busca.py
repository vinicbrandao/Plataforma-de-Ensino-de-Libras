from django.core.paginator import Page, Paginator
from django.db.models import QuerySet

from ..models import Sinal
from ..normalizacao import TextoNormalizado

SINAIS_POR_PAGINA = 20


class DicionarioService:
    """Busca de sinais pelo aluno (RF010)."""

    @staticmethod
    def tem_criterio(
        texto: str = "", categoria_id: int | None = None, somente_favoritos: bool = False
    ) -> bool:
        """A busca é obrigatória sem categoria nem filtro de favoritos (RF010 ¹, RF017 ²)."""
        return bool(texto.strip()) or categoria_id is not None or somente_favoritos

    @staticmethod
    def filtrar(
        queryset: QuerySet[Sinal], texto: str = "", categoria_id: int | None = None
    ) -> QuerySet[Sinal]:
        normalizado = TextoNormalizado.de(texto).valor
        if normalizado:
            queryset = queryset.filter(termo_normalizado__contains=normalizado)
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id, categoria__ativa=True)
        return queryset

    @classmethod
    def buscar(
        cls,
        texto: str = "",
        categoria_id: int | None = None,
        pagina: int | str = 1,
        aluno=None,
        somente_favoritos: bool = False,
    ) -> Page:
        sinais = Sinal.objects.filter(ativo=True).select_related("categoria").order_by("termo")
        if somente_favoritos:
            # Só sinais ativos: o favorito de um sinal inativado volta se ele for reativado (RF017).
            sinais = sinais.filter(favoritos__aluno=aluno)
        sinais = cls.filtrar(sinais, texto, categoria_id)
        return Paginator(sinais, SINAIS_POR_PAGINA).get_page(pagina)
