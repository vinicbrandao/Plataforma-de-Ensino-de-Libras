"""Registro de login e logout de administradores (RS009).

O login do Admin é uma view do Django, então os sinais são o ponto comum aos dois
logins. Os receptores apenas chamam o service, sem regra de negócio.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import RegistroAuditoria
from .services import AuditoriaService


@receiver(user_logged_in, dispatch_uid="contas_registrar_login_admin")
def registrar_login_admin(sender, request, user, **kwargs) -> None:
    if user.is_staff:
        AuditoriaService.registrar(user, RegistroAuditoria.Acao.LOGIN_ADMIN)


@receiver(user_logged_out, dispatch_uid="contas_registrar_logout_admin")
def registrar_logout_admin(sender, request, user, **kwargs) -> None:
    if user is not None and user.is_staff:
        AuditoriaService.registrar(user, RegistroAuditoria.Acao.LOGOUT_ADMIN)
