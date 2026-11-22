from typing import ClassVar

from django.db import IntegrityError, models, transaction

from ..exceptions import ErroDeDicionario
from ..normalizacao import TextoNormalizado


class CadastroComNomeUnicoService:
    """Base dos cadastros com um texto único sem diferenciar maiúsculas e acentos (RF015 ¹).

    As subclasses informam o model e os campos, e podem acrescentar regras em
    `validar_regras`, que `salvar` chama antes de gravar.
    """

    modelo: ClassVar[type[models.Model]]
    campo: ClassVar[str]
    campo_normalizado: ClassVar[str]
    excecao_duplicado: ClassVar[type[ErroDeDicionario]]

    @classmethod
    def validar_unico(cls, valor: str, ignorar_pk: int | None = None) -> None:
        filtro = {cls.campo_normalizado: TextoNormalizado.de(valor).valor}
        if cls.modelo.objects.filter(**filtro).exclude(pk=ignorar_pk).exists():
            raise cls.excecao_duplicado

    @classmethod
    def validar_regras(cls, objeto: models.Model) -> None:
        """Gancho para regras específicas de cada cadastro."""

    @classmethod
    def salvar(cls, objeto: models.Model) -> models.Model:
        valor = getattr(objeto, cls.campo)
        setattr(objeto, cls.campo_normalizado, TextoNormalizado.de(valor).valor)
        cls.validar_regras(objeto)
        cls.validar_unico(valor, ignorar_pk=objeto.pk)
        try:
            with transaction.atomic():
                objeto.save()
        except IntegrityError as exc:
            # Outro registro igual pode ter sido gravado entre a verificação e o save.
            raise cls.excecao_duplicado from exc
        return objeto
