from django import forms

from ..services.historico import FiltrosHistorico, OpcoesHistorico

APROVADO = "aprovado"
REPROVADO = "reprovado"
FORMATOS_DE_DATA = ["%Y-%m-%d", "%d/%m/%Y"]


def _foi_aprovado(valor: str) -> bool:
    return valor == APROVADO


def _campo_data(rotulo: str) -> forms.DateField:
    campo = forms.DateField(
        label=rotulo,
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=FORMATOS_DE_DATA,
    )
    campo.error_messages["invalid"] = "Data inválida"
    return campo


class FiltroHistoricoForm(forms.Form):
    """Filtros do histórico (RF012). As opções vêm do HistoricoService, pela view."""

    modulo = forms.TypedChoiceField(label="Módulo", required=False, coerce=int, empty_value=None)
    aula = forms.TypedChoiceField(label="Aula", required=False, coerce=int, empty_value=None)
    resultado = forms.TypedChoiceField(
        label="Resultado",
        required=False,
        choices=[("", "Todos"), (APROVADO, "Aprovado"), (REPROVADO, "Reprovado")],
        coerce=_foi_aprovado,
        empty_value=None,
    )
    data_inicial = _campo_data("Data inicial")
    data_final = _campo_data("Data final")

    def __init__(self, *args, opcoes: OpcoesHistorico | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        opcoes = opcoes or OpcoesHistorico(modulos=[], aulas=[])
        self.fields["modulo"].choices = [("", "Todos"), *opcoes.modulos]
        self.fields["aula"].choices = [("", "Todas"), *opcoes.aulas]

    def filtros(self) -> FiltrosHistorico:
        dados = self.cleaned_data
        return FiltrosHistorico(
            modulo_id=dados["modulo"],
            aula_id=dados["aula"],
            aprovada=dados["resultado"],
            data_inicial=dados["data_inicial"],
            data_final=dados["data_final"],
        )
