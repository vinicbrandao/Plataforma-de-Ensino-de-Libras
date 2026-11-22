from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from ..forms import BuscaSinalForm
from ..services import CategoriaService, DicionarioService


class BuscaView(LoginRequiredMixin, View):
    """Busca de sinais do dicionário, só para usuários autenticados (RF010)."""

    def get(self, request):
        form = BuscaSinalForm(request.GET, categorias=CategoriaService.opcoes_ativas())
        pagina = None
        if form.is_valid():
            pagina = DicionarioService.buscar(
                texto=form.cleaned_data["busca"],
                categoria_id=form.cleaned_data["categoria"],
                pagina=request.GET.get("pagina", 1),
            )
        filtros = request.GET.copy()
        filtros.pop("pagina", None)
        contexto = {"form": form, "pagina": pagina, "filtros": filtros.urlencode()}
        return render(request, "dicionario/busca.html", contexto)
