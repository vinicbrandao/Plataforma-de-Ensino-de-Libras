from django.contrib.auth.backends import ModelBackend

from .exceptions import CredenciaisInvalidas, LoginBloqueado, UsuarioDesativado
from .services import AutenticacaoService


class EmailOuCpfBackend(ModelBackend):
    """Usa as regras do AutenticacaoService também no login do Django Admin."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        login = username if username is not None else kwargs.get("email")
        if login is None or password is None:
            return None
        try:
            return AutenticacaoService.autenticar(login, password)
        except (CredenciaisInvalidas, LoginBloqueado, UsuarioDesativado):
            return None
