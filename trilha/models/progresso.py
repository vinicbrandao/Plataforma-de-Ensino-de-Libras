from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .aula import Aula
from .modulo import Modulo


class StatusProgresso(models.TextChoices):
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    CONCLUIDA = "CONCLUIDA", "Concluída"


class ProgressoAula(models.Model):
    """Andamento de um aluno em uma aula. Sem registro, a aula está Não iniciada (RF006).

    A trigger trg_progresso_conclusao preenche `concluida_em` e impede que uma aula
    concluída volte a outro status (ADR 0006).
    """

    # No módulo porque a class Meta não enxerga os atributos da classe.
    Status = StatusProgresso

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="progressos"
    )
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT, related_name="progressos")
    status = models.CharField(max_length=20, choices=Status, default=Status.EM_ANDAMENTO)
    iniciada_em = models.DateTimeField("iniciada em", default=timezone.now)
    ultimo_acesso_em = models.DateTimeField("último acesso em", default=timezone.now)
    concluida_em = models.DateTimeField("concluída em", null=True, blank=True)

    class Meta:
        verbose_name = "progresso em aula"
        verbose_name_plural = "progressos em aulas"
        constraints = [
            models.UniqueConstraint(fields=["aluno", "aula"], name="progresso_unico_por_aula"),
            models.CheckConstraint(
                condition=Q(status="CONCLUIDA", concluida_em__isnull=False)
                | (~Q(status="CONCLUIDA") & Q(concluida_em__isnull=True)),
                name="progresso_conclusao_coerente",
            ),
            models.CheckConstraint(
                condition=Q(status__in=StatusProgresso.values),
                name="trilha_progressoaula_status_valido",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.aluno} · {self.aula} · {self.get_status_display()}"


class ProgressoModulo(models.Model):
    """Leitura da view vw_progresso_modulo, criada por SQL na migração (ADR 0006)."""

    pk = models.CompositePrimaryKey("aluno", "modulo")
    aluno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    modulo = models.ForeignKey(Modulo, on_delete=models.DO_NOTHING)
    aulas_publicadas = models.IntegerField()
    aulas_concluidas = models.IntegerField()
    percentual = models.IntegerField()

    class Meta:
        managed = False
        db_table = "vw_progresso_modulo"

    def __str__(self) -> str:
        return f"{self.aluno} · {self.modulo} · {self.percentual}%"
