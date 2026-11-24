from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import GreaterThanOrEqual
from django.utils import timezone

from trilha.models import Aula

TAMANHO_MINIMO_DA_MENSAGEM = 10


# No módulo porque a class Meta não enxerga os atributos da classe.
class AssuntoMensagem(models.TextChoices):
    DUVIDA = "DUVIDA", "Dúvida"
    PROBLEMA_TECNICO = "PROBLEMA_TECNICO", "Problema técnico"
    ERRO_CONTEUDO = "ERRO_CONTEUDO", "Erro em conteúdo"
    SUGESTAO = "SUGESTAO", "Sugestão"


class SituacaoMensagem(models.TextChoices):
    ABERTA = "ABERTA", "Aberta"
    EM_ANALISE = "EM_ANALISE", "Em análise"
    RESOLVIDA = "RESOLVIDA", "Resolvida"


class MensagemContato(models.Model):
    """Mensagem do aluno à equipe e a resposta dela (RF020, spec 0010). Texto puro (RS013)."""

    Assunto = AssuntoMensagem
    Situacao = SituacaoMensagem

    # Mensagens de usuários desativados são mantidas (RF020).
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mensagens_contato"
    )
    assunto = models.CharField(max_length=20, choices=AssuntoMensagem)
    aula = models.ForeignKey(
        Aula,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensagens_contato",
        verbose_name="aula relacionada",
    )
    mensagem = models.CharField(max_length=1000)
    situacao = models.CharField(
        "situação", max_length=20, choices=SituacaoMensagem, default=SituacaoMensagem.ABERTA
    )
    resposta = models.CharField(max_length=1000, blank=True)
    enviada_em = models.DateTimeField("enviada em", default=timezone.now)
    resolvida_em = models.DateTimeField("resolvida em", null=True, blank=True)

    class Meta:
        verbose_name = "mensagem do fale conosco"
        verbose_name_plural = "mensagens do fale conosco"
        indexes = [
            models.Index(fields=["situacao", "enviada_em"], name="mensagem_fila_idx"),
            models.Index(fields=["aluno", "enviada_em"], name="mensagem_aluno_data_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(assunto__in=AssuntoMensagem.values),
                name="contato_mensagemcontato_assunto_valido",
            ),
            models.CheckConstraint(
                condition=Q(situacao__in=SituacaoMensagem.values),
                name="contato_mensagemcontato_situacao_valido",
            ),
            models.CheckConstraint(
                condition=GreaterThanOrEqual(Length("mensagem"), TAMANHO_MINIMO_DA_MENSAGEM),
                name="mensagem_tamanho_minimo",
            ),
            models.CheckConstraint(
                condition=(
                    Q(situacao=SituacaoMensagem.RESOLVIDA, resolvida_em__isnull=False) & ~Q(resposta="")
                )
                | (~Q(situacao=SituacaoMensagem.RESOLVIDA) & Q(resolvida_em__isnull=True)),
                name="mensagem_resolucao_coerente",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_assunto_display()} · {self.aluno}"
