from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db.models import Q

from ..exceptions import AulaNaoEncontrada, AulaRestritaAVisitante
from ..models import Aula, MaterialComplementar
from .progresso import ProgressoService
from .trilha import NAO_INICIADA, ROTULOS_DE_STATUS, TrilhaService


@dataclass(frozen=True)
class AulaAberta:
    aula: Aula
    materiais: tuple[MaterialComplementar, ...]
    status: str
    proxima: Aula | None
    legenda_ativa: bool
    eh_aluno: bool
    eh_visitante: bool

    @property
    def rotulo_do_status(self) -> str:
        return ROTULOS_DE_STATUS[self.status]

    @property
    def concluida(self) -> bool:
        return self.status == "CONCLUIDA"


class ExibicaoAulaService:
    """Abre uma aula para o visitante, o aluno ou o administrador (RF006, RF007)."""

    @classmethod
    def abrir(cls, aula_id: int, usuario) -> AulaAberta:
        aula = cls._buscar(aula_id)
        autenticado = usuario.is_authenticated
        administrador = autenticado and usuario.is_staff
        if not aula.publicada and not administrador:
            raise AulaNaoEncontrada
        if not autenticado:
            liberada = TrilhaService.aula_liberada_ao_visitante()
            if liberada is None or liberada.pk != aula.pk:
                raise AulaRestritaAVisitante

        eh_aluno = autenticado and not administrador
        status = NAO_INICIADA
        if eh_aluno:
            status = ProgressoService.registrar_acesso(usuario, aula).status
        auditiva = get_user_model().Deficiencia.AUDITIVA
        return AulaAberta(
            aula=aula,
            materiais=tuple(aula.materiais.all()),
            status=status,
            proxima=cls.proxima_aula(aula),
            legenda_ativa=eh_aluno and usuario.deficiencia == auditiva,
            eh_aluno=eh_aluno,
            eh_visitante=not autenticado,
        )

    @staticmethod
    def _buscar(aula_id: int) -> Aula:
        try:
            return Aula.objects.select_related("modulo").get(pk=aula_id)
        except Aula.DoesNotExist as exc:
            raise AulaNaoEncontrada from exc

    @staticmethod
    def proxima_aula(aula: Aula) -> Aula | None:
        posicao_modulo = aula.modulo.posicao
        return (
            Aula.objects.filter(publicada=True)
            .filter(
                Q(modulo__posicao=posicao_modulo, posicao__gt=aula.posicao)
                | Q(modulo__posicao__gt=posicao_modulo)
            )
            .order_by("modulo__posicao", "posicao")
            .first()
        )
