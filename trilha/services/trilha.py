from dataclasses import dataclass

from django.db.models import Prefetch

from ..models import Aula, Modulo, ProgressoAula, ProgressoModulo

NAO_INICIADA = "NAO_INICIADA"
ROTULOS_DE_STATUS = {
    NAO_INICIADA: "Não iniciada",
    ProgressoAula.Status.EM_ANDAMENTO: "Em andamento",
    ProgressoAula.Status.CONCLUIDA: "Concluída",
}
# Resposta "Teve contato com Libras" (RF001) → ordem do módulo recomendado (RF006).
ORDEM_RECOMENDADA = {"NUNCA": 1, "POUCOS_SINAIS": 1, "BASICO": 2, "EXPERIENTE": 3}


@dataclass(frozen=True)
class AulaNaTrilha:
    aula: Aula
    status: str
    liberada: bool

    @property
    def rotulo_do_status(self) -> str:
        return ROTULOS_DE_STATUS[self.status]


@dataclass(frozen=True)
class ModuloNaTrilha:
    modulo: Modulo
    ordem: int
    aulas: tuple[AulaNaTrilha, ...]
    publicadas: int
    concluidas: int
    percentual: int
    recomendado: bool


@dataclass(frozen=True)
class Trilha:
    modulos: tuple[ModuloNaTrilha, ...]
    eh_aluno: bool
    publicadas: int = 0
    concluidas: int = 0
    percentual: int = 0
    ordem_recomendada: int | None = None
    continuar: Aula | None = None


def _eh_aluno(usuario) -> bool:
    return usuario is not None and usuario.is_authenticated and not usuario.is_staff


class TrilhaService:
    """Monta a trilha de módulos e aulas publicadas, com o progresso do aluno (RF006)."""

    @staticmethod
    def aula_liberada_ao_visitante() -> Aula | None:
        return Aula.objects.filter(publicada=True).order_by("modulo__posicao", "posicao").first()

    @staticmethod
    def ordem_recomendada(contato_libras: str, total_de_modulos: int) -> int | None:
        if total_de_modulos == 0:
            return None
        return min(ORDEM_RECOMENDADA.get(contato_libras, 1), total_de_modulos)

    @staticmethod
    def _modulos_publicados() -> list[Modulo]:
        aulas_publicadas = Aula.objects.filter(publicada=True).order_by("posicao")
        return list(
            Modulo.objects.filter(aulas__publicada=True)
            .distinct()
            .order_by("posicao")
            .prefetch_related(Prefetch("aulas", queryset=aulas_publicadas, to_attr="publicadas"))
        )

    @classmethod
    def montar(cls, usuario) -> Trilha:
        modulos = cls._modulos_publicados()
        if not _eh_aluno(usuario):
            return cls._montar_sem_progresso(modulos, liberar_tudo=bool(usuario and usuario.is_authenticated))

        progressos = {
            p["aula_id"]: p
            for p in ProgressoAula.objects.filter(aluno=usuario, aula__publicada=True).values(
                "aula_id", "status", "ultimo_acesso_em"
            )
        }
        resumo = {linha.modulo_id: linha for linha in ProgressoModulo.objects.filter(aluno=usuario)}
        ordem_recomendada = cls.ordem_recomendada(usuario.contato_libras, len(modulos))

        itens = []
        for ordem, modulo in enumerate(modulos, start=1):
            aulas = tuple(
                AulaNaTrilha(
                    aula=aula,
                    status=progressos.get(aula.pk, {}).get("status", NAO_INICIADA),
                    liberada=True,
                )
                for aula in modulo.publicadas
            )
            linha = resumo.get(modulo.pk)
            itens.append(
                ModuloNaTrilha(
                    modulo=modulo,
                    ordem=ordem,
                    aulas=aulas,
                    publicadas=linha.aulas_publicadas if linha else len(aulas),
                    concluidas=linha.aulas_concluidas if linha else 0,
                    percentual=linha.percentual if linha else 0,
                    recomendado=ordem == ordem_recomendada,
                )
            )

        publicadas = sum(m.publicadas for m in itens)
        concluidas = sum(m.concluidas for m in itens)
        return Trilha(
            modulos=tuple(itens),
            eh_aluno=True,
            publicadas=publicadas,
            concluidas=concluidas,
            percentual=round(100 * concluidas / publicadas) if publicadas else 0,
            ordem_recomendada=ordem_recomendada,
            continuar=cls.aula_para_continuar(itens, progressos, ordem_recomendada),
        )

    @classmethod
    def _montar_sem_progresso(cls, modulos: list[Modulo], *, liberar_tudo: bool) -> Trilha:
        primeira = modulos[0].publicadas[0].pk if modulos else None
        itens = tuple(
            ModuloNaTrilha(
                modulo=modulo,
                ordem=ordem,
                aulas=tuple(
                    AulaNaTrilha(aula=aula, status=NAO_INICIADA, liberada=liberar_tudo or aula.pk == primeira)
                    for aula in modulo.publicadas
                ),
                publicadas=len(modulo.publicadas),
                concluidas=0,
                percentual=0,
                recomendado=False,
            )
            for ordem, modulo in enumerate(modulos, start=1)
        )
        return Trilha(modulos=itens, eh_aluno=False)

    @staticmethod
    def aula_para_continuar(
        modulos: list[ModuloNaTrilha], progressos: dict, ordem_recomendada: int | None
    ) -> Aula | None:
        em_andamento = [p for p in progressos.values() if p["status"] == ProgressoAula.Status.EM_ANDAMENTO]
        if em_andamento:
            mais_recente = max(em_andamento, key=lambda p: p["ultimo_acesso_em"])["aula_id"]
            for modulo in modulos:
                for item in modulo.aulas:
                    if item.aula.pk == mais_recente:
                        return item.aula
        recomendado = [m for m in modulos if m.ordem == ordem_recomendada]
        for modulo in [*recomendado, *modulos]:
            for item in modulo.aulas:
                if item.status != ProgressoAula.Status.CONCLUIDA:
                    return item.aula
        return None
