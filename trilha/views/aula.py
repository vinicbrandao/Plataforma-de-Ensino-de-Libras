from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import render
from django.views import View

from ..exceptions import AulaNaoEncontrada, AulaRestritaAVisitante
from ..forms import AnotacaoForm, AvaliacaoForm
from ..services import AulaAberta, ExibicaoAulaService


def pedir_login(request, mensagem: str = "Faça login para acessar esta aula"):
    messages.info(request, mensagem)
    return redirect_to_login(request.get_full_path())


def renderizar_aula(
    request,
    aula_aberta: AulaAberta,
    anotacao_form: AnotacaoForm | None = None,
    avaliacao_form: AvaliacaoForm | None = None,
):
    """Monta a tela da aula. Os forms com erro vêm das views de anotação e avaliação."""
    if anotacao_form is None:
        texto = aula_aberta.anotacao.texto if aula_aberta.anotacao else ""
        anotacao_form = AnotacaoForm(initial={"texto": texto})
    if avaliacao_form is None:
        avaliacao = aula_aberta.avaliacao
        inicial = {"nota": avaliacao.nota, "comentario": avaliacao.comentario} if avaliacao else {}
        avaliacao_form = AvaliacaoForm(initial=inicial)
    contexto = {
        "aula_aberta": aula_aberta,
        "anotacao_form": anotacao_form,
        "avaliacao_form": avaliacao_form,
    }
    return render(request, "trilha/aula.html", contexto)


class AulaView(View):
    """Vídeo-aula (RF007). O visitante só abre a primeira aula da trilha (RF006)."""

    def get(self, request, aula_id):
        try:
            aula_aberta = ExibicaoAulaService.abrir(aula_id, request.user)
        except AulaNaoEncontrada as exc:
            raise Http404 from exc
        except AulaRestritaAVisitante:
            return pedir_login(request)
        return renderizar_aula(request, aula_aberta)
