from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from contas.views.acesso import SomenteAlunoMixin

from ..exceptions import LimiteDiarioAtingido
from ..forms import MensagemContatoForm
from ..services import MensagemService


class FaleConoscoView(SomenteAlunoMixin, View):
    """Envio de dúvidas, sugestões e relatos de problemas (RF020)."""

    template = "contato/fale_conosco.html"

    def get(self, request):
        form = MensagemContatoForm(aulas=MensagemService.aulas_disponiveis())
        return render(request, self.template, {"form": form})

    def post(self, request):
        form = MensagemContatoForm(request.POST, aulas=MensagemService.aulas_disponiveis())
        if form.is_valid():
            dados = form.cleaned_data
            try:
                MensagemService.enviar(request.user, dados["assunto"], dados["aula"], dados["mensagem"])
            except LimiteDiarioAtingido as exc:
                form.add_error(None, exc.mensagem)
            else:
                messages.success(request, "Mensagem enviada. Acompanhe a resposta em Minhas mensagens")
                return redirect("contato:minhas")
        return render(request, self.template, {"form": form})


class MinhasMensagensView(SomenteAlunoMixin, View):
    """Mensagens do próprio aluno, com a situação e a resposta (RF020, RS004)."""

    def get(self, request):
        pagina = MensagemService.do_aluno(request.user, request.GET.get("pagina", 1))
        return render(request, "contato/minhas_mensagens.html", {"pagina": pagina})
