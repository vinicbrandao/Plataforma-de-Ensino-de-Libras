from django.db import IntegrityError, transaction

from ..exceptions import SinalNaoEncontrado
from ..models import Favorito, Sinal


class FavoritoService:
    """Sinais favoritos do aluno (RF017). Toda consulta parte do próprio aluno (RS004)."""

    @staticmethod
    def alternar(aluno, sinal_id: int) -> bool:
        """Favorita ou desfavorita o sinal e devolve se ele ficou favorito."""
        if not Sinal.objects.filter(pk=sinal_id, ativo=True).exists():
            raise SinalNaoEncontrado
        apagados, _ = Favorito.objects.filter(aluno=aluno, sinal_id=sinal_id).delete()
        if apagados:
            return False
        try:
            with transaction.atomic():
                Favorito.objects.create(aluno=aluno, sinal_id=sinal_id)
        except IntegrityError:
            # Dois cliques ao mesmo tempo: o outro já criou o favorito.
            pass
        return True

    @staticmethod
    def ids_dos_favoritos(aluno, sinal_ids) -> set[int]:
        return set(
            Favorito.objects.filter(aluno=aluno, sinal_id__in=list(sinal_ids)).values_list(
                "sinal_id", flat=True
            )
        )

    @staticmethod
    def tem_favoritos(aluno) -> bool:
        return Favorito.objects.filter(aluno=aluno).exists()
