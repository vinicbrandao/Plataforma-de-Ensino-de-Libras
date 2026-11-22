from django.shortcuts import render
from django.views import View

from ..services import TrilhaService


class TrilhaView(View):
    """Página inicial: a trilha de módulos e aulas, com o progresso do aluno (RF006)."""

    def get(self, request):
        trilha = TrilhaService.montar(request.user)
        return render(request, "trilha/trilha.html", {"trilha": trilha})
