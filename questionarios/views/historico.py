from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from ..exceptions import PeriodoInvalido
from ..forms import FiltroHistoricoForm
from ..services import HistoricoService


class HistoricoView(LoginRequiredMixin, View):
    """Histórico dos questionários do aluno autenticado (RF012)."""

    def get(self, request):
        form = FiltroHistoricoForm(request.GET, opcoes=HistoricoService.opcoes(request.user))
        historico = None
        if form.is_valid():
            try:
                historico = HistoricoService.consultar(
                    request.user, form.filtros(), pagina=request.GET.get("pagina", 1)
                )
            except PeriodoInvalido as exc:
                form.add_error("data_final", exc.mensagem)
        filtros = request.GET.copy()
        filtros.pop("pagina", None)
        contexto = {
            "form": form,
            "historico": historico,
            # Sem a lista (filtros inválidos), o resumo e o aviso de vazio continuam valendo.
            "resumo": historico.resumo if historico else HistoricoService.resumo_por_aula(request.user),
            "filtros": filtros.urlencode(),
        }
        return render(request, "questionarios/historico.html", contexto)
