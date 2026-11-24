from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count, QuerySet
from django.utils import timezone

from ..exceptions import AcaoSomenteDoAluno, AulaNaoIniciada
from ..models import Aula, AvaliacaoAula, ProgressoAula
from .exibicao import ExibicaoAulaService

UMA_CASA = Decimal("0.1")


@dataclass(frozen=True)
class ResumoAvaliacoes:
    media: Decimal | None
    quantidade: int
    comentarios: tuple[tuple[datetime, int, str], ...]


class AvaliacaoService:
    """Avaliação da aula pelo aluno e consulta das médias pelo administrador (RF018)."""

    @staticmethod
    def obter(aluno, aula) -> AvaliacaoAula | None:
        return AvaliacaoAula.objects.filter(aluno=aluno, aula=aula).first()

    @staticmethod
    def avaliar(aluno, aula_id: int, nota: int, comentario: str = "") -> tuple[AvaliacaoAula, bool]:
        """Cria ou substitui a avaliação do aluno e devolve se ela foi criada agora."""
        aula = ExibicaoAulaService.verificar_acesso(aula_id, aluno)
        if aluno.is_staff:
            raise AcaoSomenteDoAluno
        # Abrir a aula já a deixa Em andamento; sem progresso, ela nunca foi aberta.
        if not ProgressoAula.objects.filter(aluno=aluno, aula=aula).exists():
            raise AulaNaoIniciada
        return AvaliacaoAula.objects.update_or_create(
            aluno=aluno,
            aula=aula,
            defaults={"nota": nota, "comentario": comentario.strip(), "avaliada_em": timezone.now()},
        )

    @staticmethod
    def arredondar(media) -> Decimal | None:
        if media is None:
            return None
        return Decimal(str(media)).quantize(UMA_CASA, rounding=ROUND_HALF_UP)

    @classmethod
    def resumo(cls, aula: Aula) -> ResumoAvaliacoes:
        """Média, quantidade e comentários, sem nenhum dado do aluno (RS004)."""
        avaliacoes = AvaliacaoAula.objects.filter(aula=aula)
        totais = avaliacoes.aggregate(media=Avg("nota"), quantidade=Count("id"))
        comentarios = tuple(
            avaliacoes.exclude(comentario="")
            .order_by("-avaliada_em")
            .values_list("avaliada_em", "nota", "comentario")
        )
        return ResumoAvaliacoes(
            media=cls.arredondar(totais["media"]),
            quantidade=totais["quantidade"],
            comentarios=comentarios,
        )

    @staticmethod
    def com_resumo(aulas: QuerySet[Aula]) -> QuerySet[Aula]:
        return aulas.annotate(
            media_avaliacoes=Avg("avaliacoes__nota"), quantidade_avaliacoes=Count("avaliacoes")
        )
