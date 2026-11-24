from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from ..exceptions import LinkInvalido, MuitasSolicitacoes, SenhaIgualAAtual
from ..forms import NovaSenhaForm, SolicitarRedefinicaoForm
from ..services import RedefinicaoSenhaService

CHAVE_DA_SESSAO = "redefinicao_codigo"
MENSAGEM_DE_ENVIO = "Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha"


class EsqueciSenhaView(View):
    """Pedido do link de redefinição de senha (RF004). A resposta não revela se o e-mail existe."""

    template = "contas/esqueci_senha.html"

    def get(self, request):
        return render(request, self.template, {"form": SolicitarRedefinicaoForm()})

    def post(self, request):
        form = SolicitarRedefinicaoForm(request.POST)
        if not form.is_valid():
            return render(request, self.template, {"form": form})

        def montar_link(codigo: str) -> str:
            return request.build_absolute_uri(reverse("contas:redefinir_senha_link", args=[codigo]))

        try:
            RedefinicaoSenhaService.solicitar(form.cleaned_data["email"], montar_link)
        except MuitasSolicitacoes as exc:
            form.add_error(None, exc.mensagem)
            return render(request, self.template, {"form": form})
        messages.info(request, MENSAGEM_DE_ENVIO)
        return redirect("contas:entrar")


class RedefinirSenhaView(View):
    """Nova senha a partir do link do e-mail (RF004).

    O código sai do endereço no primeiro acesso e fica na sessão, para não vazar
    pelo histórico do navegador nem pelo cabeçalho Referer.
    """

    template = "contas/redefinir_senha.html"

    def get(self, request, codigo=None):
        if codigo is not None:
            request.session[CHAVE_DA_SESSAO] = codigo
            return redirect("contas:redefinir_senha")
        try:
            token = RedefinicaoSenhaService.validar(request.session.get(CHAVE_DA_SESSAO, ""))
        except LinkInvalido as exc:
            return self._link_invalido(request, exc)
        return render(request, self.template, {"form": NovaSenhaForm(usuario=token.usuario)})

    def post(self, request, codigo=None):
        codigo = request.session.get(CHAVE_DA_SESSAO, "")
        try:
            token = RedefinicaoSenhaService.validar(codigo)
        except LinkInvalido as exc:
            return self._link_invalido(request, exc)
        form = NovaSenhaForm(request.POST, usuario=token.usuario)
        if not form.is_valid():
            return render(request, self.template, {"form": form})
        try:
            RedefinicaoSenhaService.redefinir(codigo, form.cleaned_data["nova_senha"])
        except SenhaIgualAAtual as exc:
            form.add_error("nova_senha", exc.mensagem)
            return render(request, self.template, {"form": form})
        except LinkInvalido as exc:
            return self._link_invalido(request, exc)
        request.session.pop(CHAVE_DA_SESSAO, None)
        messages.success(request, "Senha alterada com sucesso")
        return redirect("contas:entrar")

    def _link_invalido(self, request, exc: LinkInvalido):
        request.session.pop(CHAVE_DA_SESSAO, None)
        return render(request, self.template, {"link_invalido": exc.mensagem}, status=400)
