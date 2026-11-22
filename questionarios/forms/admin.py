from django import forms
from django.core.exceptions import ValidationError

from ..exceptions import ErroDeQuestionario
from ..models import Questao
from ..services import QuestaoService


class QuestaoAdminForm(forms.ModelForm):
    class Meta:
        model = Questao
        fields = ["aula", "enunciado", "sinal", "posicao"]

    def clean(self) -> dict:
        dados = super().clean()
        if dados.get("aula") and dados.get("posicao"):
            try:
                QuestaoService.validar_posicao(dados["aula"].pk, dados["posicao"], self.instance.pk)
            except ErroDeQuestionario as exc:
                self.add_error("posicao", exc.mensagem)
        return dados


class AlternativasFormSet(forms.BaseInlineFormSet):
    """Valida o conjunto de alternativas pelo QuestaoService (RF014)."""

    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return
        corretas = [
            bool(form.cleaned_data.get("correta"))
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE")
        ]
        try:
            QuestaoService.validar_alternativas(corretas)
        except ErroDeQuestionario as exc:
            raise ValidationError(exc.mensagem) from exc
