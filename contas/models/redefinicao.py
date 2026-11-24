from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .usuario import Usuario


class TokenRedefinicaoSenha(models.Model):
    """Código de uso único do link de redefinição de senha (RF004, RS008).

    Guarda só o SHA-256 do código: o código em si existe apenas no e-mail.
    """

    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="tokens_redefinicao"
    )
    codigo_hash = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField("criado em", default=timezone.now)
    expira_em = models.DateTimeField("expira em")
    usado_em = models.DateTimeField("usado em", null=True, blank=True)
    invalidado_em = models.DateTimeField("invalidado em", null=True, blank=True)

    class Meta:
        verbose_name = "token de redefinição de senha"
        verbose_name_plural = "tokens de redefinição de senha"
        constraints = [
            models.CheckConstraint(
                condition=Q(expira_em__gt=F("criado_em")), name="token_expira_depois_de_criado"
            ),
        ]

    def __str__(self) -> str:
        return f"Redefinição de {self.usuario} em {self.criado_em:%d/%m/%Y %H:%M}"


class SolicitacaoRedefinicao(models.Model):
    """Pedido de redefinição, exista o e-mail ou não (RF004).

    A chave é um HMAC do e-mail, para não guardar e-mails digitados que não existem.
    """

    chave = models.CharField(max_length=64)
    criada_em = models.DateTimeField("criada em", default=timezone.now)

    class Meta:
        verbose_name = "solicitação de redefinição"
        verbose_name_plural = "solicitações de redefinição"
        indexes = [models.Index(fields=["chave", "criada_em"], name="solicitacao_chave_data_idx")]

    def __str__(self) -> str:
        return f"Solicitação em {self.criada_em:%d/%m/%Y %H:%M}"
