from abc import ABC, abstractmethod

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from ..exceptions import AcaoSomenteDoAluno, AulaNaoEncontrada, AulaNaoIniciada, AulaRestritaAVisitante
from ..forms import AnotacaoForm, AvaliacaoForm
from ..services import AnotacaoService, AvaliacaoService, ExibicaoAulaService
from .aula import pedir_login, renderizar_aula


def _voltar_para_a_aula(aula_id: int, ancora: str):
    return redirect(f"{reverse('trilha:aula', args=[aula_id])}#{ancora}")


class ParticipacaoNaAulaMixin(LoginRequiredMixin, ABC):
    """Ações do aluno na tela da aula: converte as exceções de domínio em respostas.

    Cada view concreta implementa `executar`; o `post` é o mesmo para todas.
    """

    def post(self, request, aula_id):
        try:
            return self.executar(request, aula_id)
        except AulaNaoEncontrada as exc:
            raise Http404 from exc
        except AulaRestritaAVisitante:
            return pedir_login(request)
        except AcaoSomenteDoAluno as exc:
            raise PermissionDenied from exc

    @abstractmethod
    def executar(self, request, aula_id):
        """Faz a ação da view e devolve a resposta HTTP."""

    @staticmethod
    def reapresentar(request, aula_id, **forms):
        aula_aberta = ExibicaoAulaService.abrir(aula_id, request.user)
        return renderizar_aula(request, aula_aberta, **forms)


class AnotacaoView(ParticipacaoNaAulaMixin, View):
    """Salva a anotação do aluno na aula (RF019)."""

    def executar(self, request, aula_id):
        form = AnotacaoForm(request.POST)
        if not form.is_valid():
            return self.reapresentar(request, aula_id, anotacao_form=form)
        AnotacaoService.salvar(request.user, aula_id, form.cleaned_data["texto"])
        messages.success(request, "Anotação salva")
        return _voltar_para_a_aula(aula_id, "anotacoes")


class ExcluirAnotacaoView(ParticipacaoNaAulaMixin, View):
    """Exclui a anotação do aluno na aula, de forma definitiva (RF019)."""

    def executar(self, request, aula_id):
        AnotacaoService.excluir(request.user, aula_id)
        messages.success(request, "Anotação excluída")
        return _voltar_para_a_aula(aula_id, "anotacoes")


class AvaliacaoView(ParticipacaoNaAulaMixin, View):
    """Cria ou substitui a avaliação do aluno na aula (RF018)."""

    def executar(self, request, aula_id):
        form = AvaliacaoForm(request.POST)
        if not form.is_valid():
            return self.reapresentar(request, aula_id, avaliacao_form=form)
        try:
            _, criada = AvaliacaoService.avaliar(
                request.user, aula_id, form.cleaned_data["nota"], form.cleaned_data["comentario"]
            )
        except AulaNaoIniciada as exc:
            form.add_error(None, exc.mensagem)
            return self.reapresentar(request, aula_id, avaliacao_form=form)
        messages.success(request, "Obrigado pela sua avaliação!" if criada else "Avaliação atualizada")
        return _voltar_para_a_aula(aula_id, "avaliacao")
