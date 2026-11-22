from django import forms

from ..exceptions import ErroDeTrilha
from ..models import Aula, Modulo
from ..services import AulaService, ModuloService


class ConteudoOrdenadoAdminForm(forms.ModelForm):
    """Base dos forms do Admin: valida título e posição pelo service, com mensagem no campo."""

    service = None

    def escopo(self, dados: dict) -> dict:
        return {}

    def clean(self) -> dict:
        dados = super().clean()
        escopo = self.escopo(dados)
        if escopo is None:
            return dados
        validacoes = {
            "titulo": lambda: self.service.validar_titulo(dados["titulo"], escopo, self.instance.pk),
            "posicao": lambda: self.service.validar_posicao(dados["posicao"], escopo, self.instance.pk),
        }
        for campo, validar in validacoes.items():
            if campo in dados:
                self._aplicar(campo, validar)
        return dados

    def _aplicar(self, campo: str, validar) -> None:
        try:
            validar()
        except ErroDeTrilha as exc:
            self.add_error(campo, exc.mensagem)


class ModuloAdminForm(ConteudoOrdenadoAdminForm):
    service = ModuloService

    class Meta:
        model = Modulo
        fields = ["titulo", "descricao", "posicao"]


class AulaAdminForm(ConteudoOrdenadoAdminForm):
    service = AulaService

    class Meta:
        model = Aula
        fields = [
            "modulo", "titulo", "descricao", "posicao", "video", "legenda", "texto_apoio", "publicada"
        ]

    def escopo(self, dados: dict) -> dict | None:
        modulo = dados.get("modulo")
        return {"modulo_id": modulo.pk} if modulo else None

    def clean(self) -> dict:
        dados = super().clean()
        if "video" in dados and "legenda" in dados:
            self._aplicar(
                "publicada",
                lambda: AulaService.validar_publicacao(
                    dados.get("publicada", False),
                    tem_video=bool(dados["video"]),
                    tem_legenda=bool(dados["legenda"]),
                    tem_questao=AulaService.tem_questao(self.instance.pk),
                ),
            )
        return dados
