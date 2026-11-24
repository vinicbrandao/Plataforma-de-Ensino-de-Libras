from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from .usuario import Usuario


# No módulo porque a class Meta não enxerga os atributos da classe.
class VinculoResponsavel(models.TextChoices):
    PAI = "PAI", "Pai"
    MAE = "MAE", "Mãe"
    TUTOR = "TUTOR", "Tutor ou guardião legal"


class ResponsavelLegal(models.Model):
    """Responsável pelo aluno menor de idade (RF002). Não acessa o sistema; só recebe e-mails.

    CPF e e-mail não são únicos: o mesmo responsável pode ter mais de um aluno.
    """

    Vinculo = VinculoResponsavel

    aluno = models.OneToOneField(Usuario, on_delete=models.PROTECT, related_name="responsavel")
    nome = models.CharField("nome do responsável", max_length=120)
    vinculo = models.CharField("vínculo", max_length=20, choices=VinculoResponsavel)
    cpf = models.CharField("CPF do responsável", max_length=14)
    email = models.EmailField("e-mail do responsável", max_length=200)
    telefone = models.CharField("telefone do responsável", max_length=15)
    termo_aceito_em = models.DateTimeField("termo de autorização aceito em")

    class Meta:
        verbose_name = "responsável legal"
        verbose_name_plural = "responsáveis legais"
        constraints = [
            models.CheckConstraint(
                condition=Q(vinculo__in=VinculoResponsavel.values),
                name="contas_responsavellegal_vinculo_valido",
            ),
            models.CheckConstraint(
                condition=Q(cpf__regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"),
                name="responsavel_cpf_formatado",
            ),
            models.CheckConstraint(condition=Q(email=Lower("email")), name="responsavel_email_minusculo"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.get_vinculo_display()})"
