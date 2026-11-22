from django.core.paginator import Page, Paginator
from django.db.models import QuerySet

from ..models import Sinal
from ..normalizacao import TextoNormalizado

SINAIS_POR_PAGINA = 20


class DicionarioService:
    """Busca de sinais pelo aluno (RF010)."""

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
    def buscar(cls, texto: str = "", categoria_id: int | None = None, pagina: int | str = 1) -> Page:
        sinais = Sinal.objects.filter(ativo=True).select_related("categoria").order_by("termo")
        sinais = cls.filtrar(sinais, texto, categoria_id)
        return Paginator(sinais, SINAIS_POR_PAGINA).get_page(pagina)
