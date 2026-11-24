from collections.abc import Callable
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from ..exceptions import LinkInvalido, MuitasSolicitacoes, SenhaIgualAAtual
from ..models import SolicitacaoRedefinicao, TokenRedefinicaoSenha, Usuario
from .codigos import gerar_codigo, hash_do_codigo

VALIDADE_DO_LINK = timedelta(minutes=30)
JANELA_DO_LIMITE = timedelta(hours=1)
LIMITE_POR_HORA = 3


class RedefinicaoSenhaService:
    """Recuperação de senha por link de uso único enviado ao e-mail (RF004, RS002, RS008)."""

    @staticmethod
    def normalizar_email(email: str) -> str:
        return (email or "").strip().lower()

    @staticmethod
    def chave(email_normalizado: str) -> str:
        return salted_hmac("contas.redefinicao", email_normalizado, algorithm="sha256").hexdigest()

    @classmethod
    def solicitar(cls, email: str, montar_link: Callable[[str], str]) -> None:
        """Registra o pedido e, só para usuário ativo, envia o link. A resposta da view é sempre a mesma."""
        email = cls.normalizar_email(email)
        chave = cls.chave(email)
        agora = timezone.now()
        recentes = SolicitacaoRedefinicao.objects.filter(chave=chave, criada_em__gt=agora - JANELA_DO_LIMITE)
        if recentes.count() >= LIMITE_POR_HORA:
            raise MuitasSolicitacoes
        SolicitacaoRedefinicao.objects.create(chave=chave, criada_em=agora)

        usuario = Usuario.objects.filter(email=email, is_active=True).first()
        if usuario is None:
            return
        codigo = gerar_codigo()
        with transaction.atomic():
            cls._tokens_abertos(usuario).update(invalidado_em=agora)
            TokenRedefinicaoSenha.objects.create(
                usuario=usuario, codigo_hash=hash_do_codigo(codigo), criado_em=agora, expira_em=agora + VALIDADE_DO_LINK
            )
        link = montar_link(codigo)
        transaction.on_commit(lambda: cls._enviar_link(usuario, link))

    @staticmethod
    def _tokens_abertos(usuario: Usuario):
        return TokenRedefinicaoSenha.objects.filter(usuario=usuario, usado_em__isnull=True, invalidado_em__isnull=True)

    @staticmethod
    def validar(codigo: str, para_atualizar: bool = False) -> TokenRedefinicaoSenha:
        tokens = TokenRedefinicaoSenha.objects.select_related("usuario")
        if para_atualizar:
            tokens = tokens.select_for_update(of=("self",))
        token = tokens.filter(codigo_hash=hash_do_codigo(codigo)).first()
        valido = (
            token is not None
            and token.usado_em is None
            and token.invalidado_em is None
            and token.expira_em > timezone.now()
            and token.usuario.is_active
        )
        if not valido:
            raise LinkInvalido
        return token

    @classmethod
    def redefinir(cls, codigo: str, nova_senha: str) -> Usuario:
        with transaction.atomic():
            token = cls.validar(codigo, para_atualizar=True)
            usuario = token.usuario
            if usuario.check_password(nova_senha):
                raise SenhaIgualAAtual
            # Trocar a senha muda o hash de sessão: o Django encerra as outras sessões (RF004).
            usuario.set_password(nova_senha)
            usuario.save(update_fields=["password"])
            agora = timezone.now()
            token.usado_em = agora
            token.save(update_fields=["usado_em"])
            cls._tokens_abertos(usuario).update(invalidado_em=agora)
        transaction.on_commit(lambda: cls._avisar_alteracao(usuario))
        return usuario

    @staticmethod
    def _enviar_link(usuario: Usuario, link: str) -> None:
        send_mail(
            "Redefinição de senha · Plataforma de Ensino de Libras",
            f"Olá, {usuario.nome_completo}.\n\n"
            f"Para criar uma nova senha, abra o link abaixo. Ele vale por 30 minutos e só pode ser usado uma vez.\n\n"
            f"{link}\n\n"
            "Se você não pediu a redefinição, ignore este e-mail. Sua senha continua a mesma.",
            None,
            [usuario.email],
        )

    @staticmethod
    def _avisar_alteracao(usuario: Usuario) -> None:
        send_mail(
            "Sua senha foi alterada · Plataforma de Ensino de Libras",
            f"Olá, {usuario.nome_completo}.\n\n"
            "A senha da sua conta foi alterada, e as sessões abertas foram encerradas. "
            "Se não foi você, peça uma nova redefinição de senha.",
            None,
            [usuario.email],
        )
