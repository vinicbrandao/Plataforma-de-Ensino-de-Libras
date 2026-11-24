from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from ..exceptions import (
    CpfDoResponsavelIgualAoDoAluno,
    EmailJaCadastrado,
    LinkConfirmacaoInvalido,
    ResponsavelSomenteLeitura,
    SenhaAtualIncorreta,
    SenhaIgualAAtual,
)
from ..forms import FotoForm, PerfilForm, ResponsavelForm, TrocaSenhaForm
from ..services import PerfilService
from .acesso import SomenteAlunoMixin

DADOS_ATUALIZADOS = "Dados atualizados com sucesso"
TEMPLATE_PERFIL = "contas/perfil.html"


def _dados_iniciais(usuario) -> dict:
    campos = ("nome_completo", "email", "telefone", "deficiencia", "qual_deficiencia", "contato_libras")
    return {**{campo: getattr(usuario, campo) for campo in campos}, "receber_lembretes": usuario.receber_lembretes}


def _renderizar_perfil(request, perfil_form=None, foto_form=None, responsavel_form=None):
    responsavel = PerfilService.responsavel_de(request.user)
    editavel = responsavel is not None and PerfilService.eh_menor(request.user)
    if editavel and responsavel_form is None:
        campos = ("nome", "vinculo", "cpf", "email", "telefone")
        responsavel_form = ResponsavelForm(initial={campo: getattr(responsavel, campo) for campo in campos})
    contexto = {
        "perfil_form": perfil_form or PerfilForm(initial=_dados_iniciais(request.user)),
        "foto_form": foto_form or FotoForm(),
        "responsavel": responsavel,
        "responsavel_form": responsavel_form if editavel else None,
    }
    return render(request, TEMPLATE_PERFIL, contexto)


class PerfilView(SomenteAlunoMixin, View):
    """Consulta e alteração dos dados do próprio aluno (RF005). Sem id na rota: sempre request.user."""

    def get(self, request):
        return _renderizar_perfil(request)

    def post(self, request):
        form = PerfilForm(request.POST)
        if not form.is_valid():
            return _renderizar_perfil(request, perfil_form=form)

        def montar_link(codigo: str) -> str:
            return request.build_absolute_uri(reverse("contas:confirmar_email", args=[codigo]))

        try:
            email_pendente = PerfilService.atualizar(request.user, form.dados(), montar_link)
        except EmailJaCadastrado:
            form.add_error("email", "E-mail já cadastrado")
            return _renderizar_perfil(request, perfil_form=form)
        messages.success(request, DADOS_ATUALIZADOS)
        if email_pendente:
            messages.info(request, "Enviamos um link de confirmação para o novo e-mail")
        return redirect("contas:perfil")


class FotoView(SomenteAlunoMixin, View):
    """Envio da foto de perfil (RF005)."""

    def post(self, request):
        form = FotoForm(request.POST, request.FILES)
        if not form.is_valid():
            return _renderizar_perfil(request, foto_form=form)
        PerfilService.trocar_foto(request.user, form.cleaned_data["foto"])
        messages.success(request, DADOS_ATUALIZADOS)
        return redirect("contas:perfil")


class TrocaSenhaView(SomenteAlunoMixin, View):
    """Troca de senha mediante a senha atual (RF005, RS007)."""

    template = "contas/trocar_senha.html"

    def get(self, request):
        return render(request, self.template, {"form": TrocaSenhaForm(usuario=request.user)})

    def post(self, request):
        form = TrocaSenhaForm(request.POST, usuario=request.user)
        if not form.is_valid():
            return render(request, self.template, {"form": form})
        try:
            PerfilService.trocar_senha(
                request.user, form.cleaned_data["senha_atual"], form.cleaned_data["nova_senha"]
            )
        except SenhaAtualIncorreta as exc:
            form.add_error("senha_atual", exc.mensagem)
            return render(request, self.template, {"form": form})
        except SenhaIgualAAtual as exc:
            form.add_error("nova_senha", exc.mensagem)
            return render(request, self.template, {"form": form})
        # Mantém esta sessão aberta depois da troca do hash da senha.
        update_session_auth_hash(request, request.user)
        messages.success(request, "Senha alterada com sucesso")
        return redirect("contas:perfil")


class ConfirmarEmailView(View):
    """Confirmação do novo e-mail pelo link enviado a ele (RF005, RS011)."""

    def get(self, request, codigo):
        try:
            PerfilService.confirmar_email(codigo)
        except (LinkConfirmacaoInvalido, EmailJaCadastrado):
            contexto = {"mensagem": LinkConfirmacaoInvalido.mensagem}
            return render(request, "contas/link_invalido.html", contexto, status=400)
        messages.success(request, DADOS_ATUALIZADOS)
        return redirect("contas:perfil" if request.user.is_authenticated else "contas:entrar")


class ResponsavelView(SomenteAlunoMixin, View):
    """Alteração dos dados do responsável pelo aluno menor (RF002, RF005)."""

    def post(self, request):
        form = ResponsavelForm(request.POST)
        if not form.is_valid():
            return _renderizar_perfil(request, responsavel_form=form)
        try:
            PerfilService.atualizar_responsavel(request.user, form.dados())
        except ResponsavelSomenteLeitura as exc:
            raise PermissionDenied from exc
        except CpfDoResponsavelIgualAoDoAluno as exc:
            form.add_error("cpf", exc.mensagem)
            return _renderizar_perfil(request, responsavel_form=form)
        messages.success(request, DADOS_ATUALIZADOS)
        return redirect("contas:perfil")
