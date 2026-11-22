from django import forms

from ..models import Questao


class QuestionarioForm(forms.Form):
    """Um campo por questão, com as alternativas como opções (RF009).

    Os campos são opcionais: exigir todas as respostas é regra do QuestionarioService.
    """

    def __init__(self, *args, questoes: tuple[Questao, ...] = (), **kwargs):
        super().__init__(*args, **kwargs)
        self.questoes = questoes
        for questao in questoes:
            self.fields[self.nome_do_campo(questao)] = forms.TypedChoiceField(
                label=questao.enunciado,
                choices=[(a.pk, a.texto) for a in questao.alternativas.all()],
                coerce=int,
                required=False,
                empty_value=None,
                widget=forms.RadioSelect,
            )

    @staticmethod
    def nome_do_campo(questao: Questao) -> str:
        return f"questao_{questao.pk}"

    def campos_por_questao(self):
        return [(questao, self[self.nome_do_campo(questao)]) for questao in self.questoes]

    def respostas(self) -> dict[int, int]:
        respostas = {}
        for questao in self.questoes:
            escolhida = self.cleaned_data.get(self.nome_do_campo(questao))
            if escolhida is not None:
                respostas[questao.pk] = escolhida
        return respostas
