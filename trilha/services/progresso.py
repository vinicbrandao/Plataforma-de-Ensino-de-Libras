from django.db import transaction
from django.utils import timezone

from ..models import Aula, ProgressoAula


class ProgressoService:
    """Andamento do aluno nas aulas (RF006, RF007).

    A data de conclusão é preenchida pela trigger trg_progresso_conclusao (ADR 0006).
    """

    @staticmethod
    def registrar_acesso(aluno, aula: Aula) -> ProgressoAula:
        agora = timezone.now()
        progresso, criado = ProgressoAula.objects.get_or_create(
            aluno=aluno, aula=aula, defaults={"iniciada_em": agora, "ultimo_acesso_em": agora}
        )
        if not criado:
            progresso.ultimo_acesso_em = agora
            progresso.save(update_fields=["ultimo_acesso_em"])
        return progresso

    @staticmethod
    def concluir(aluno, aula: Aula) -> ProgressoAula:
        """Conclui a aula para o aluno. Chamado pelo questionário na aprovação (ADR 0008)."""
        with transaction.atomic():
            progresso, _ = ProgressoAula.objects.select_for_update().get_or_create(
                aluno=aluno, aula=aula
            )
            if progresso.status != ProgressoAula.Status.CONCLUIDA:
                progresso.status = ProgressoAula.Status.CONCLUIDA
                progresso.save(update_fields=["status"])
        progresso.refresh_from_db(fields=["concluida_em"])
        return progresso
