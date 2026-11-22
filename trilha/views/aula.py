from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import render
from django.views import View

from ..exceptions import AulaNaoEncontrada, AulaRestritaAVisitante
from ..services import ExibicaoAulaService


class AulaView(View):
    """Vídeo-aula (RF007). O visitante só abre a primeira aula da trilha (RF006)."""

    def get(self, request, aula_id):
        try:
            aula_aberta = ExibicaoAulaService.abrir(aula_id, request.user)
        except AulaNaoEncontrada as exc:
            raise Http404 from exc
        except AulaRestritaAVisitante:
            messages.info(request, "Faça login para acessar esta aula")
            return redirect_to_login(request.get_full_path())
        return render(request, "trilha/aula.html", {"aula_aberta": aula_aberta})
