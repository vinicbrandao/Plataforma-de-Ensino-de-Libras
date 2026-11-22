from django.db import models


class FalhaLogin(models.Model):
    """Falhas consecutivas de login para uma chave (RS001).

    A chave é um HMAC do login normalizado, para não guardar o CPF ou o e-mail digitado.
    """

    chave = models.CharField(max_length=64, unique=True)
    falhas = models.PositiveSmallIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "falha de login"
        verbose_name_plural = "falhas de login"

    def __str__(self) -> str:
        return f"{self.falhas} falha(s)"
