from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from ..exceptions import CpfDoResponsavelIgualAoDoAluno, CpfJaCadastrado, EmailJaCadastrado, ResponsavelObrigatorio
from ..forms import CadastroForm
from ..services import CadastroService

BACKEND = "contas.backends.EmailOuCpfBackend"
TEMPLATE = "contas/cadastro.html"


class CadastroView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("inicio")
        return render(request, TEMPLATE, {"form": CadastroForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("inicio")
        form = CadastroForm(request.POST)
        if not form.is_valid():
            return render(request, TEMPLATE, {"form": form})
        try:
            usuario = CadastroService.cadastrar(form.dados(), form.responsavel())
        except EmailJaCadastrado:
            form.add_error("email", "E-mail já cadastrado")
        except CpfJaCadastrado:
            form.add_error("cpf", "CPF já cadastrado")
        except CpfDoResponsavelIgualAoDoAluno as exc:
            form.add_error("responsavel_cpf", exc.mensagem)
        except ResponsavelObrigatorio as exc:
            form.add_error(None, exc.mensagem)
        else:
            login(request, usuario, backend=BACKEND)
            messages.success(request, "Cadastro realizado com sucesso")
            return redirect("inicio")
        return render(request, TEMPLATE, {"form": form})
