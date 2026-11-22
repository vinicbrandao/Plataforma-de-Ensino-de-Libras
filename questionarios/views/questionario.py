from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import render
from django.views import View

from trilha.exceptions import AulaNaoEncontrada, AulaRestritaAVisitante

from ..exceptions import QuestionarioSemQuestoes, RespostasIncompletas
from ..forms import QuestionarioForm
from ..services import QuestionarioService

TEMPLATE_QUESTIONARIO = "questionarios/questionario.html"
TEMPLATE_RESULTADO = "questionarios/resultado.html"


class QuestionarioView(View):
    """Questionário da aula (RF009). As regras de acesso são as da aula (RF006)."""

    def get(self, request, aula_id):
        try:
            questionario = QuestionarioService.carregar(aula_id, request.user)
        except AulaNaoEncontrada as exc:
            raise Http404 from exc
        except AulaRestritaAVisitante:
            return self._pedir_login(request)
        form = QuestionarioForm(questoes=questionario.questoes)
        return render(request, TEMPLATE_QUESTIONARIO, {"questionario": questionario, "form": form})

    def post(self, request, aula_id):
        try:
            questionario = QuestionarioService.carregar(aula_id, request.user)
        except AulaNaoEncontrada as exc:
            raise Http404 from exc
        except AulaRestritaAVisitante:
            return self._pedir_login(request)
        form = QuestionarioForm(request.POST, questoes=questionario.questoes)
        if form.is_valid():
            try:
                resultado = QuestionarioService.corrigir(aula_id, request.user, form.respostas())
            except (RespostasIncompletas, QuestionarioSemQuestoes) as exc:
                form.add_error(None, exc.mensagem)
            else:
                # Sem redirecionamento: a tentativa do visitante não é gravada (spec 0004).
                return render(request, TEMPLATE_RESULTADO, {"resultado": resultado})
        return render(request, TEMPLATE_QUESTIONARIO, {"questionario": questionario, "form": form})

    @staticmethod
    def _pedir_login(request):
        messages.info(request, "Faça login para acessar esta aula")
        return redirect_to_login(request.get_full_path())
