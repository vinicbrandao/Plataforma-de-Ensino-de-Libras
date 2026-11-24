from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from ..forms import BuscaSinalForm
from ..services import CategoriaService, DicionarioService, FavoritoService


class BuscaView(LoginRequiredMixin, View):
    """Busca de sinais do dicionário (RF010), com o filtro de favoritos do aluno (RF017)."""

    def get(self, request):
        form = BuscaSinalForm(request.GET, categorias=CategoriaService.opcoes_ativas())
        eh_aluno = not request.user.is_staff
        pagina = None
        favoritos: set[int] = set()
        somente_favoritos = False
        if form.is_valid():
            dados = form.cleaned_data
            somente_favoritos = dados["favoritos"] and eh_aluno
            if DicionarioService.tem_criterio(dados["busca"], dados["categoria"], somente_favoritos):
                pagina = DicionarioService.buscar(
                    texto=dados["busca"],
                    categoria_id=dados["categoria"],
                    pagina=request.GET.get("pagina", 1),
                    aluno=request.user,
                    somente_favoritos=somente_favoritos,
                )
                if eh_aluno:
                    favoritos = FavoritoService.ids_dos_favoritos(
                        request.user, (sinal.pk for sinal in pagina)
                    )
        filtros = request.GET.copy()
        filtros.pop("pagina", None)
        contexto = {
            "form": form,
            "pagina": pagina,
            "filtros": filtros.urlencode(),
            "eh_aluno": eh_aluno,
            "favoritos": favoritos,
            "sem_favoritos": somente_favoritos and not FavoritoService.tem_favoritos(request.user),
        }
        return render(request, "dicionario/busca.html", contexto)
