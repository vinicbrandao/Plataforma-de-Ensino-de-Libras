from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .usuario import Usuario


class HistoricoAlteracao(models.Model):
    """Alteração do perfil, com os valores anterior e novo (RF005, RS007).

    Nenhum service altera nem exclui estas linhas. A troca de senha fica sem valores (RS003).
    """

    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="historico")
    campo = models.CharField(max_length=60)
    valor_anterior = models.CharField("valor anterior", max_length=255, blank=True)
    valor_novo = models.CharField("valor novo", max_length=255, blank=True)
    alterado_em = models.DateTimeField("alterado em", default=timezone.now)

    class Meta:
        verbose_name = "alteração do perfil"
        verbose_name_plural = "histórico de alterações do perfil"
        ordering = ["-alterado_em", "-id"]

    def __str__(self) -> str:
        return f"{self.usuario} · {self.campo}"


class ConfirmacaoEmail(models.Model):
    """Troca de e-mail pendente até a confirmação pelo novo endereço (RF005, RS011)."""

    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="confirmacoes_email")
    novo_email = models.EmailField("novo e-mail", max_length=200)
    codigo_hash = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField("criado em", default=timezone.now)
    expira_em = models.DateTimeField("expira em")
    confirmado_em = models.DateTimeField("confirmado em", null=True, blank=True)
    invalidado_em = models.DateTimeField("invalidado em", null=True, blank=True)

    class Meta:
        verbose_name = "confirmação de e-mail"
        verbose_name_plural = "confirmações de e-mail"
        constraints = [
            models.CheckConstraint(
                condition=Q(expira_em__gt=F("criado_em")), name="confirmacao_expira_depois_de_criada"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.usuario} → {self.novo_email}"
