from django.contrib.auth import login
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from ..exceptions import CredenciaisInvalidas, LoginBloqueado, UsuarioDesativado
from ..forms import EntrarForm
from ..services import AutenticacaoService

BACKEND = "contas.backends.EmailOuCpfBackend"
TEMPLATE = "contas/entrar.html"
MENSAGENS = {
    CredenciaisInvalidas: "Login ou senha inválidos",
    LoginBloqueado: "Muitas tentativas de acesso. Tente novamente em 15 minutos",
    UsuarioDesativado: "Usuário desativado",
}


def _destino_seguro(request: HttpRequest, destino: str | None) -> str | None:
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return None


class EntrarView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("inicio")
        contexto = {
            "form": EntrarForm(),
            "next": _destino_seguro(request, request.GET.get("next")),
        }
        return render(request, TEMPLATE, contexto)

    def post(self, request):
        destino = _destino_seguro(request, request.POST.get("next"))
        form = EntrarForm(request.POST)
        if not form.is_valid():
            return render(request, TEMPLATE, {"form": form, "next": destino})
        try:
            usuario = AutenticacaoService.autenticar(
                form.cleaned_data["login"], form.cleaned_data["senha"]
            )
        except (CredenciaisInvalidas, LoginBloqueado, UsuarioDesativado) as exc:
            form.add_error(None, MENSAGENS[type(exc)])
            return render(request, TEMPLATE, {"form": form, "next": destino})
        login(request, usuario, backend=BACKEND)
        padrao = reverse("admin:index") if usuario.is_staff else reverse("inicio")
        # HttpResponseRedirect, e não redirect(): redirect() tentaria resolver um
        # `next` sem barra como nome de rota.
        return HttpResponseRedirect(destino or padrao)
