from .cadastro import CadastroView
from .entrar import EntrarView
from .perfil import ConfirmarEmailView, FotoView, PerfilView, ResponsavelView, TrocaSenhaView
from .redefinicao import EsqueciSenhaView, RedefinirSenhaView
from .sair import SairView

__all__ = [
    "CadastroView",
    "ConfirmarEmailView",
    "EntrarView",
    "EsqueciSenhaView",
    "FotoView",
    "PerfilView",
    "RedefinirSenhaView",
    "ResponsavelView",
    "SairView",
    "TrocaSenhaView",
]
