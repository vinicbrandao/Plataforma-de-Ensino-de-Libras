from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from ..exceptions import SinalNaoEncontrado
from ..services import FavoritoService


class FavoritoView(LoginRequiredMixin, View):
    """Favorita ou desfavorita um sinal do dicionário (RF017)."""

    def post(self, request, sinal_id):
        if request.user.is_staff:
            # Os favoritos são do aluno (RS004).
            raise PermissionDenied
        try:
            favorito = FavoritoService.alternar(request.user, sinal_id)
        except SinalNaoEncontrado as exc:
            raise Http404 from exc
        mensagem = "Sinal adicionado aos favoritos" if favorito else "Sinal removido dos favoritos"
        messages.success(request, mensagem)
        return redirect(self._destino(request))

    @staticmethod
    def _destino(request) -> str:
        proxima = request.POST.get("proxima", "")
        seguro = url_has_allowed_host_and_scheme(
            proxima, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        )
        return proxima if seguro else "dicionario:busca"
