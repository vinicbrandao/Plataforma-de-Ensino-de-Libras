from django.core.paginator import Page, Paginator
from django.db.models import Case, IntegerField, QuerySet, Value, When
from django.utils import timezone

from trilha.models import Aula

from ..exceptions import LimiteDiarioAtingido, MensagemJaResolvida, RespostaObrigatoria
from ..models import MensagemContato, SituacaoMensagem

LIMITE_DIARIO = 5
MENSAGENS_POR_PAGINA = 20


class MensagemService:
    """Fale conosco: envio pelo aluno e resposta pelo administrador (RF020)."""

    @staticmethod
    def aulas_disponiveis() -> list[tuple[str, list[tuple[int, str]]]]:
        """Aulas publicadas, agrupadas pelo módulo, no formato de choices agrupadas."""
        grupos: dict[str, list[tuple[int, str]]] = {}
        aulas = Aula.objects.filter(publicada=True).select_related("modulo").order_by("modulo__posicao", "posicao")
        for aula in aulas:
            grupos.setdefault(aula.modulo.titulo, []).append((aula.pk, aula.titulo))
        return list(grupos.items())

    @staticmethod
    def enviar(aluno, assunto: str, aula_id: int | None, mensagem: str) -> MensagemContato:
        # O dia é o local (TIME_ZONE): __date converte o horário antes de comparar.
        hoje = timezone.localdate()
        if MensagemContato.objects.filter(aluno=aluno, enviada_em__date=hoje).count() >= LIMITE_DIARIO:
            raise LimiteDiarioAtingido
        return MensagemContato.objects.create(
            aluno=aluno, assunto=assunto, aula_id=aula_id, mensagem=mensagem
        )

    @staticmethod
    def do_aluno(aluno, pagina: int | str = 1) -> Page:
        mensagens = (
            MensagemContato.objects.filter(aluno=aluno)
            .select_related("aula")
            .order_by("-enviada_em", "-id")
        )
        return Paginator(mensagens, MENSAGENS_POR_PAGINA).get_page(pagina)

    @staticmethod
    def validar_atualizacao(situacao_atual: str, nova_situacao: str, resposta: str) -> None:
        if situacao_atual == SituacaoMensagem.RESOLVIDA and nova_situacao != SituacaoMensagem.RESOLVIDA:
            raise MensagemJaResolvida
        if nova_situacao == SituacaoMensagem.RESOLVIDA and not resposta.strip():
            raise RespostaObrigatoria

    @classmethod
    def atualizar(cls, mensagem: MensagemContato, situacao_anterior: str) -> MensagemContato:
        """Grava a situação e a resposta definidas pelo administrador (RF020)."""
        cls.validar_atualizacao(situacao_anterior, mensagem.situacao, mensagem.resposta)
        mensagem.resposta = mensagem.resposta.strip()
        if mensagem.situacao == SituacaoMensagem.RESOLVIDA and mensagem.resolvida_em is None:
            mensagem.resolvida_em = timezone.now()
        mensagem.save(update_fields=["situacao", "resposta", "resolvida_em"])
        return mensagem

    @staticmethod
    def fila() -> QuerySet[MensagemContato]:
        """Não resolvidas primeiro; dentro de cada grupo, as mais antigas primeiro."""
        resolvida = Case(
            When(situacao=SituacaoMensagem.RESOLVIDA, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        return (
            MensagemContato.objects.select_related("aluno", "aula")
            .annotate(resolvida=resolvida)
            .order_by("resolvida", "enviada_em")
        )
