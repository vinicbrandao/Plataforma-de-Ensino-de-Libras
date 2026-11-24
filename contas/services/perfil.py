from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from ..exceptions import (
    CpfDoResponsavelIgualAoDoAluno,
    EmailJaCadastrado,
    LinkConfirmacaoInvalido,
    ResponsavelSomenteLeitura,
    SenhaAtualIncorreta,
    SenhaIgualAAtual,
)
from ..models import ConfirmacaoEmail, HistoricoAlteracao, ResponsavelLegal, Usuario
from .cadastro import CadastroService, DadosResponsavel
from .codigos import gerar_codigo, hash_do_codigo

VALIDADE_DA_CONFIRMACAO = timedelta(hours=24)
CAMPOS_EDITAVEIS = (
    "nome_completo",
    "telefone",
    "deficiencia",
    "qual_deficiencia",
    "contato_libras",
    "receber_lembretes",
)


@dataclass(frozen=True)
class DadosPerfil:
    nome_completo: str
    email: str
    telefone: str
    deficiencia: str
    qual_deficiencia: str
    contato_libras: str
    receber_lembretes: bool


def _texto(valor) -> str:
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    return str(valor)


class PerfilService:
    """Consulta e alteração dos dados do próprio aluno, com histórico (RF005, RS004, RS007, RS011)."""

    @staticmethod
    def registrar(usuario: Usuario, campo: str, anterior="", novo="") -> None:
        HistoricoAlteracao.objects.create(
            usuario=usuario, campo=campo, valor_anterior=_texto(anterior)[:255], valor_novo=_texto(novo)[:255]
        )

    @classmethod
    def atualizar(cls, usuario: Usuario, dados: DadosPerfil, montar_link: Callable[[str], str]) -> bool:
        """Grava os campos alterados e devolve se ficou um e-mail novo esperando confirmação."""
        email_novo = dados.email != usuario.email
        if email_novo and Usuario.objects.filter(email=dados.email).exclude(pk=usuario.pk).exists():
            raise EmailJaCadastrado
        alterados = []
        with transaction.atomic():
            for campo in CAMPOS_EDITAVEIS:
                novo = getattr(dados, campo)
                anterior = getattr(usuario, campo)
                if novo != anterior:
                    cls.registrar(usuario, campo, anterior, novo)
                    setattr(usuario, campo, novo)
                    alterados.append(campo)
            if alterados:
                usuario.save(update_fields=alterados)
            if email_novo:
                cls._pedir_confirmacao(usuario, dados.email, montar_link)
        return email_novo

    @staticmethod
    def _pedir_confirmacao(usuario: Usuario, novo_email: str, montar_link: Callable[[str], str]) -> None:
        agora = timezone.now()
        ConfirmacaoEmail.objects.filter(
            usuario=usuario, confirmado_em__isnull=True, invalidado_em__isnull=True
        ).update(invalidado_em=agora)
        codigo = gerar_codigo()
        ConfirmacaoEmail.objects.create(
            usuario=usuario,
            novo_email=novo_email,
            codigo_hash=hash_do_codigo(codigo),
            criado_em=agora,
            expira_em=agora + VALIDADE_DA_CONFIRMACAO,
        )
        link = montar_link(codigo)
        transaction.on_commit(
            lambda: send_mail(
                "Confirme o novo e-mail · Plataforma de Ensino de Libras",
                f"Olá, {usuario.nome_completo}.\n\n"
                "Para confirmar este endereço como o e-mail da sua conta, abra o link abaixo. "
                f"Ele vale por 24 horas. Até a confirmação, o e-mail anterior continua valendo.\n\n{link}",
                None,
                [novo_email],
            )
        )

    @classmethod
    def confirmar_email(cls, codigo: str) -> Usuario:
        with transaction.atomic():
            confirmacao = (
                ConfirmacaoEmail.objects.select_for_update(of=("self",))
                .select_related("usuario")
                .filter(codigo_hash=hash_do_codigo(codigo))
                .first()
            )
            valida = (
                confirmacao is not None
                and confirmacao.confirmado_em is None
                and confirmacao.invalidado_em is None
                and confirmacao.expira_em > timezone.now()
            )
            if not valida:
                raise LinkConfirmacaoInvalido
            usuario = confirmacao.usuario
            if Usuario.objects.filter(email=confirmacao.novo_email).exclude(pk=usuario.pk).exists():
                raise EmailJaCadastrado
            anterior = usuario.email
            usuario.email = confirmacao.novo_email
            usuario.save(update_fields=["email"])
            cls.registrar(usuario, "email", anterior, usuario.email)
            confirmacao.confirmado_em = timezone.now()
            confirmacao.save(update_fields=["confirmado_em"])
        transaction.on_commit(lambda: cls._avisar_email_anterior(usuario, anterior))
        return usuario

    @staticmethod
    def _avisar_email_anterior(usuario: Usuario, anterior: str) -> None:
        send_mail(
            "O e-mail da sua conta mudou · Plataforma de Ensino de Libras",
            f"Olá, {usuario.nome_completo}.\n\n"
            "O e-mail da sua conta foi alterado, e este endereço deixou de ser usado. "
            "Se não foi você, entre em contato com a equipe.",
            None,
            [anterior],
        )

    @classmethod
    def trocar_senha(cls, usuario: Usuario, senha_atual: str, nova_senha: str) -> None:
        if not usuario.check_password(senha_atual):
            raise SenhaAtualIncorreta
        if senha_atual == nova_senha:
            raise SenhaIgualAAtual
        with transaction.atomic():
            usuario.set_password(nova_senha)
            usuario.save(update_fields=["password"])
            # Só a data: senhas não entram no histórico (RS003, RS007).
            cls.registrar(usuario, "senha")

    @classmethod
    def trocar_foto(cls, usuario: Usuario, arquivo) -> None:
        anterior = usuario.foto.name if usuario.foto else ""
        with transaction.atomic():
            usuario.foto = arquivo
            usuario.save(update_fields=["foto"])
            cls.registrar(usuario, "foto", anterior, usuario.foto.name)
        if anterior:
            armazenamento = usuario.foto.storage
            transaction.on_commit(lambda: armazenamento.delete(anterior))

    @staticmethod
    def eh_menor(usuario: Usuario) -> bool:
        """Calculado pela data de nascimento a cada acesso, sem a rotina diária (RF002 simplificado)."""
        return usuario.data_nascimento is not None and CadastroService.eh_menor(usuario.data_nascimento)

    @staticmethod
    def responsavel_de(usuario: Usuario) -> ResponsavelLegal | None:
        return ResponsavelLegal.objects.filter(aluno=usuario).first()

    @classmethod
    def atualizar_responsavel(cls, aluno: Usuario, dados: DadosResponsavel) -> None:
        """Só enquanto o aluno for menor. Cada campo alterado vai ao histórico, e o responsável é avisado."""
        responsavel = cls.responsavel_de(aluno)
        if responsavel is None or not cls.eh_menor(aluno):
            raise ResponsavelSomenteLeitura
        if dados.cpf == aluno.cpf:
            raise CpfDoResponsavelIgualAoDoAluno
        email_anterior = responsavel.email
        alterados = []
        with transaction.atomic():
            for campo in ("nome", "vinculo", "cpf", "email", "telefone"):
                novo = getattr(dados, campo)
                anterior = getattr(responsavel, campo)
                if novo != anterior:
                    cls.registrar(aluno, f"responsavel.{campo}", anterior, novo)
                    setattr(responsavel, campo, novo)
                    alterados.append(campo)
            if alterados:
                responsavel.save(update_fields=alterados)
        if not alterados:
            return
        destinatarios = [email_anterior] + ([responsavel.email] if responsavel.email != email_anterior else [])
        transaction.on_commit(lambda: cls._avisar_responsavel(aluno, responsavel, destinatarios))

    @staticmethod
    def _avisar_responsavel(aluno: Usuario, responsavel: ResponsavelLegal, destinatarios: list[str]) -> None:
        # Sem dados sensíveis, como a deficiência (RF002, RS006).
        send_mail(
            "Dados do responsável alterados · Plataforma de Ensino de Libras",
            f"Olá, {responsavel.nome}.\n\n"
            f"Os dados do responsável legal de {aluno.nome_completo} foram alterados na Plataforma de "
            "Ensino de Libras. Se você não reconhece a alteração, entre em contato com a equipe.",
            None,
            destinatarios,
        )
