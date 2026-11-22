from django.shortcuts import render
from django.views import View


class InicioView(View):
    """Página inicial provisória. A spec da trilha passa a rota `inicio` para a trilha."""

    def get(self, request):
        return render(request, "contas/inicio.html")
