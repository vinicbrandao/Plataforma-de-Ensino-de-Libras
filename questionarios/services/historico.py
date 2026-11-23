from dataclasses import dataclass
from datetime import date, datetime

from django.core.paginator import Page, Paginator
from django.db.models import Count, Min, Q

from trilha.models import Aula, Modulo

from ..exceptions import PeriodoInvalido
from ..models import Tentativa

TENTATIVAS_POR_PAGINA = 20


@dataclass(frozen=True)
class FiltrosHistorico:
    modulo_id: int | None = None
    aula_id: int | None = None
    aprovada: bool | None = None
    data_inicial: date | None = None
    data_final: date | None = None


@dataclass(frozen=True)
class OpcoesHistorico:
    modulos: list[tuple[int, str]]
    aulas: list[tuple[str, list[tuple[int, str]]]]


@dataclass(frozen=True)
class ResumoAula:
    modulo: str
    aula: str
    tentativas: int
    primeira_aprovacao: datetime | None


@dataclass(frozen=True)
class Historico:
    pagina: Page
    resumo: tuple[ResumoAula, ...]

    @property
    def vazio(self) -> bool:
        """Sem nenhuma tentativa, com ou sem filtro: o resumo tem uma linha por aula respondida."""
        return not self.resumo


class HistoricoService:
    """Histórico dos questionários do aluno (RF012).

    Toda consulta parte das tentativas do próprio aluno, então nenhum filtro alcança
    as de outra pessoa (RS004).
    """

    @staticmethod
    def _do_aluno(aluno):
        return Tentativa.objects.filter(aluno=aluno)

    @classmethod
    def opcoes(cls, aluno) -> OpcoesHistorico:
        # Só o que o aluno respondeu, inclusive aulas despublicadas depois (RF-66).
        aulas = (
            Aula.objects.filter(tentativas__aluno=aluno)
            .select_related("modulo")
            .order_by("modulo__posicao", "posicao")
            .distinct()
        )
        modulos: dict[int, Modulo] = {}
        agrupadas: dict[int, list[tuple[int, str]]] = {}
        for aula in aulas:
            modulos.setdefault(aula.modulo_id, aula.modulo)
            agrupadas.setdefault(aula.modulo_id, []).append((aula.pk, aula.titulo))
        return OpcoesHistorico(
            modulos=[(modulo.pk, modulo.titulo) for modulo in modulos.values()],
            aulas=[(modulos[modulo_id].titulo, itens) for modulo_id, itens in agrupadas.items()],
        )

    @classmethod
    def consultar(
        cls, aluno, filtros: FiltrosHistorico | None = None, pagina: int | str = 1
    ) -> Historico:
        filtros = filtros or FiltrosHistorico()
        cls._validar_periodo(filtros)
        tentativas = cls._filtrar(cls._do_aluno(aluno), filtros)
        tentativas = tentativas.select_related("aula__modulo").order_by("-realizada_em", "-id")
        return Historico(
            pagina=Paginator(tentativas, TENTATIVAS_POR_PAGINA).get_page(pagina),
            resumo=cls.resumo_por_aula(aluno),
        )

    @classmethod
    def resumo_por_aula(cls, aluno) -> tuple[ResumoAula, ...]:
        """Total de tentativas e primeira aprovação de cada aula, sem filtros (RF-65)."""
        linhas = (
            cls._do_aluno(aluno)
            .values("aula", "aula__titulo", "aula__modulo__titulo")
            .annotate(
                tentativas=Count("id"),
                primeira_aprovacao=Min("realizada_em", filter=Q(aprovada=True)),
            )
            .order_by("aula__modulo__posicao", "aula__posicao")
        )
        return tuple(
            ResumoAula(
                modulo=linha["aula__modulo__titulo"],
                aula=linha["aula__titulo"],
                tentativas=linha["tentativas"],
                primeira_aprovacao=linha["primeira_aprovacao"],
            )
            for linha in linhas
        )

    @staticmethod
    def _validar_periodo(filtros: FiltrosHistorico) -> None:
        if filtros.data_inicial and filtros.data_final and filtros.data_final < filtros.data_inicial:
            raise PeriodoInvalido

    @staticmethod
    def _filtrar(tentativas, filtros: FiltrosHistorico):
        if filtros.modulo_id is not None:
            tentativas = tentativas.filter(aula__modulo_id=filtros.modulo_id)
        if filtros.aula_id is not None:
            tentativas = tentativas.filter(aula_id=filtros.aula_id)
        if filtros.aprovada is not None:
            tentativas = tentativas.filter(aprovada=filtros.aprovada)
        # __date usa o fuso de TIME_ZONE, então o dia é o do aluno, e não o UTC.
        if filtros.data_inicial:
            tentativas = tentativas.filter(realizada_em__date__gte=filtros.data_inicial)
        if filtros.data_final:
            tentativas = tentativas.filter(realizada_em__date__lte=filtros.data_final)
        return tentativas
