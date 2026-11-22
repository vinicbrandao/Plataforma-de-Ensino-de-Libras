import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from ..documentos import Cpf
from ..exceptions import CredenciaisInvalidas, LoginBloqueado, UsuarioDesativado
from ..models import FalhaLogin, Usuario

LIMITE_DE_FALHAS = 5
TEMPO_DE_BLOQUEIO = timedelta(minutes=15)


class AutenticacaoService:
    """Login por e-mail ou CPF, com bloqueio após falhas consecutivas (RF003, RS001, RS002)."""

    @staticmethod
    def normalizar_login(login: str) -> str:
        texto = re.sub(r"\s", "", login or "")
        if "@" in texto:
            return texto.lower()
        try:
            return Cpf.de_texto(texto).formatado
        except ValueError:
            return texto

    @staticmethod
    def chave(login_normalizado: str) -> str:
        return salted_hmac(
            "contas.falha_login", login_normalizado, algorithm="sha256"
        ).hexdigest()

    @classmethod
    def autenticar(cls, login: str, senha: str) -> Usuario:
        login_normalizado = cls.normalizar_login(login)
        chave = cls.chave(login_normalizado)
        if cls.esta_bloqueado(chave):
            raise LoginBloqueado

        usuario = cls._buscar_usuario(login_normalizado)
        if usuario is None:
            # Calcula um hash mesmo assim, para que o tempo de resposta não revele que o
            # login não existe, como faz o ModelBackend do Django.
            Usuario().set_password(senha)
            cls.registrar_falha(chave)
            raise CredenciaisInvalidas
        if not usuario.check_password(senha):
            cls.registrar_falha(chave)
            raise CredenciaisInvalidas

        FalhaLogin.objects.filter(chave=chave).delete()
        if not usuario.is_active:
            raise UsuarioDesativado
        return usuario

    @staticmethod
    def _buscar_usuario(login_normalizado: str) -> Usuario | None:
        campo = "email" if "@" in login_normalizado else "cpf"
        return Usuario.objects.filter(**{campo: login_normalizado}).first()

    @staticmethod
    def esta_bloqueado(chave: str) -> bool:
        return FalhaLogin.objects.filter(chave=chave, bloqueado_ate__gt=timezone.now()).exists()

    @staticmethod
    def registrar_falha(chave: str) -> None:
        agora = timezone.now()
        with transaction.atomic():
            falha, _ = FalhaLogin.objects.select_for_update().get_or_create(chave=chave)
            if falha.bloqueado_ate and falha.bloqueado_ate <= agora:
                falha.falhas = 0
                falha.bloqueado_ate = None
            falha.falhas += 1
            if falha.falhas >= LIMITE_DE_FALHAS:
                falha.bloqueado_ate = agora + TEMPO_DE_BLOQUEIO
            falha.save(update_fields=["falhas", "bloqueado_ate"])
