import re
from typing import ClassVar

from django.db import IntegrityError, models, transaction

from ..exceptions import AulaIncompletaParaPublicar, PosicaoJaCadastrada, TituloJaCadastrado
from ..models import Aula, Modulo


class ConteudoOrdenadoService:
    """Base dos cadastros com título e posição únicos dentro de um escopo (RF013).

    As subclasses informam o model e o escopo (a trilha inteira ou o módulo), e podem
    acrescentar regras em `validar_regras`.
    """

    modelo: ClassVar[type[models.Model]]

    @classmethod
    def escopo(cls, objeto: models.Model) -> dict:
        return {}

    @staticmethod
    def normalizar_titulo(titulo: str) -> str:
        return re.sub(r"\s+", " ", titulo or "").strip()

    @classmethod
    def validar_titulo(cls, titulo: str, escopo: dict, ignorar_pk: int | None = None) -> None:
        titulo = cls.normalizar_titulo(titulo)
        repetido = cls.modelo.objects.filter(titulo__iexact=titulo, **escopo).exclude(pk=ignorar_pk)
        if repetido.exists():
            raise TituloJaCadastrado

    @classmethod
    def validar_posicao(cls, posicao: int, escopo: dict, ignorar_pk: int | None = None) -> None:
        repetida = cls.modelo.objects.filter(posicao=posicao, **escopo).exclude(pk=ignorar_pk)
        if repetida.exists():
            raise PosicaoJaCadastrada

    @classmethod
    def validar_regras(cls, objeto: models.Model) -> None:
        """Gancho para regras específicas de cada cadastro."""

    @classmethod
    def _validar(cls, objeto: models.Model) -> None:
        escopo = cls.escopo(objeto)
        cls.validar_titulo(objeto.titulo, escopo, ignorar_pk=objeto.pk)
        cls.validar_posicao(objeto.posicao, escopo, ignorar_pk=objeto.pk)
        cls.validar_regras(objeto)

    @classmethod
    def salvar(cls, objeto: models.Model) -> models.Model:
        objeto.titulo = cls.normalizar_titulo(objeto.titulo)
        cls._validar(objeto)
        try:
            with transaction.atomic():
                objeto.save()
        except IntegrityError:
            # Gravação simultânea: a nova validação identifica qual regra foi quebrada.
            cls._validar(objeto)
            raise
        return objeto


class ModuloService(ConteudoOrdenadoService):
    """Cadastro de módulos: título e posição únicos na trilha (RF013)."""

    modelo = Modulo


class AulaService(ConteudoOrdenadoService):
    """Cadastro de aulas: título e posição únicos no módulo e regras de publicação (RF013)."""

    modelo = Aula

    @classmethod
    def escopo(cls, aula: Aula) -> dict:
        return {"modulo_id": aula.modulo_id}

    @staticmethod
    def tem_questao(aula_id: int | None) -> bool:
        # Consulta pelo nome reverso "questoes", sem importar o app questionarios.
        return aula_id is not None and Aula.objects.filter(pk=aula_id, questoes__isnull=False).exists()

    @staticmethod
    def validar_publicacao(
        publicada: bool, *, tem_video: bool, tem_legenda: bool, tem_questao: bool
    ) -> None:
        if publicada and not (tem_video and tem_legenda and tem_questao):
            raise AulaIncompletaParaPublicar

    @classmethod
    def validar_regras(cls, aula: Aula) -> None:
        cls.validar_publicacao(
            aula.publicada,
            tem_video=bool(aula.video),
            tem_legenda=bool(aula.legenda),
            tem_questao=cls.tem_questao(aula.pk),
        )
