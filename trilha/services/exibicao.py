from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db.models import Q

from ..exceptions import AulaNaoEncontrada, AulaRestritaAVisitante
from ..models import AnotacaoAula, Aula, AvaliacaoAula, MaterialComplementar
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
    anotacao: AnotacaoAula | None = None
    avaliacao: AvaliacaoAula | None = None

    @property
    def rotulo_do_status(self) -> str:
        return ROTULOS_DE_STATUS[self.status]

    @property
    def concluida(self) -> bool:
        return self.status == "CONCLUIDA"


class ExibicaoAulaService:
    """Abre uma aula para o visitante, o aluno ou o administrador (RF006, RF007)."""

    @classmethod
    def verificar_acesso(cls, aula_id: int, usuario) -> Aula:
        """Aplica as regras de acesso à aula sem registrar progresso.

        Aula inexistente, ou não publicada para quem não é administrador: AulaNaoEncontrada.
        Visitante fora da primeira aula da trilha: AulaRestritaAVisitante.
        """
        aula = cls._buscar(aula_id)
        autenticado = usuario.is_authenticated
        if not aula.publicada and not (autenticado and usuario.is_staff):
            raise AulaNaoEncontrada
        if not autenticado:
            liberada = TrilhaService.aula_liberada_ao_visitante()
            if liberada is None or liberada.pk != aula.pk:
                raise AulaRestritaAVisitante
        return aula

    @classmethod
    def abrir(cls, aula_id: int, usuario) -> AulaAberta:
        aula = cls.verificar_acesso(aula_id, usuario)
        autenticado = usuario.is_authenticated
        eh_aluno = autenticado and not usuario.is_staff
        status = NAO_INICIADA
        anotacao = avaliacao = None
        if eh_aluno:
            status = ProgressoService.registrar_acesso(usuario, aula).status
            # Só do próprio aluno (RF018, RF019, RS004).
            anotacao = AnotacaoAula.objects.filter(aluno=usuario, aula=aula).first()
            avaliacao = AvaliacaoAula.objects.filter(aluno=usuario, aula=aula).first()
        auditiva = get_user_model().Deficiencia.AUDITIVA
        return AulaAberta(
            aula=aula,
            materiais=tuple(aula.materiais.all()),
            status=status,
            proxima=cls.proxima_aula(aula),
            legenda_ativa=eh_aluno and usuario.deficiencia == auditiva,
            eh_aluno=eh_aluno,
            eh_visitante=not autenticado,
            anotacao=anotacao,
            avaliacao=avaliacao,
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
