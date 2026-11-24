import re
from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.exceptions import LinkInvalido, MuitasSolicitacoes, SenhaIgualAAtual
from contas.models import TokenRedefinicaoSenha, Usuario
from contas.services import RedefinicaoSenhaService

from .fabricas import SENHA, criar_admin, criar_aluno

NOVA_SENHA = "OutraSenha456"
MENSAGEM = "Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha"


def montar_link(codigo: str) -> str:
    return f"http://testserver{reverse('contas:redefinir_senha_link', args=[codigo])}"


def codigo_do_email(mensagem) -> str:
    return re.search(r"/senha/redefinir/([^/\s]+)/", mensagem.body).group(1)


class SolicitarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def solicitar(self, email: str) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            RedefinicaoSenhaService.solicitar(email, montar_link)

    def test_so_usuario_ativo_recebe_o_email(self):
        inativo = criar_aluno(email="inativo@exemplo.com", cpf="111.444.777-35")
        Usuario.objects.filter(pk=inativo.pk).update(is_active=False)

        self.solicitar("Maria@Exemplo.com")
        self.solicitar("ninguem@exemplo.com")
        self.solicitar("inativo@exemplo.com")

        self.assertEqual([m.to for m in mail.outbox], [["maria@exemplo.com"]])
        self.assertIn("30 minutos", mail.outbox[0].body)

    def test_administrador_tambem_recupera_a_senha(self):
        criar_admin()

        self.solicitar("admin@exemplo.com")

        self.assertEqual(len(mail.outbox), 1)

    def test_quarta_solicitacao_na_hora_e_recusada_e_depois_de_uma_hora_volta(self):
        agora = timezone.now()
        with mock.patch("django.utils.timezone.now", return_value=agora):
            for _ in range(3):
                self.solicitar("ninguem@exemplo.com")
            with self.assertRaises(MuitasSolicitacoes):
                self.solicitar("ninguem@exemplo.com")
        with mock.patch("django.utils.timezone.now", return_value=agora + timedelta(hours=1, seconds=1)):
            self.solicitar("ninguem@exemplo.com")

    def test_banco_guarda_so_o_hash_do_codigo(self):
        self.solicitar("maria@exemplo.com")

        codigo = codigo_do_email(mail.outbox[0])
        token = TokenRedefinicaoSenha.objects.get()
        self.assertNotEqual(token.codigo_hash, codigo)
        self.assertEqual(len(token.codigo_hash), 64)


class RedefinirTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def novo_codigo(self) -> str:
        with self.captureOnCommitCallbacks(execute=True):
            RedefinicaoSenhaService.solicitar("maria@exemplo.com", montar_link)
        return codigo_do_email(mail.outbox[-1])

    def test_link_vale_uma_vez(self):
        codigo = self.novo_codigo()

        RedefinicaoSenhaService.redefinir(codigo, NOVA_SENHA)

        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.check_password(NOVA_SENHA))
        with self.assertRaises(LinkInvalido):
            RedefinicaoSenhaService.validar(codigo)

    def test_link_vence_em_30_minutos(self):
        codigo = self.novo_codigo()

        with mock.patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(minutes=31)):
            with self.assertRaises(LinkInvalido):
                RedefinicaoSenhaService.validar(codigo)

    def test_nova_solicitacao_invalida_o_link_anterior(self):
        primeiro = self.novo_codigo()
        segundo = self.novo_codigo()

        with self.assertRaises(LinkInvalido):
            RedefinicaoSenhaService.validar(primeiro)
        RedefinicaoSenhaService.validar(segundo)

    def test_recusa_a_senha_atual(self):
        codigo = self.novo_codigo()

        with self.assertRaises(SenhaIgualAAtual):
            RedefinicaoSenhaService.redefinir(codigo, SENHA)

    def test_avisa_por_email_depois_da_alteracao(self):
        codigo = self.novo_codigo()

        with self.captureOnCommitCallbacks(execute=True):
            RedefinicaoSenhaService.redefinir(codigo, NOVA_SENHA)

        self.assertIn("foi alterada", mail.outbox[-1].subject)


class RedefinicaoViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def pedir_link(self, email="maria@exemplo.com"):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("contas:esqueci_senha"), {"email": email}, follow=True)

    def test_mensagem_e_a_mesma_para_email_cadastrado_ou_nao(self):
        cadastrado = self.pedir_link()
        inexistente = self.pedir_link("ninguem@exemplo.com")

        self.assertContains(cadastrado, MENSAGEM)
        self.assertContains(inexistente, MENSAGEM)
        self.assertEqual(len(mail.outbox), 1)

    def test_limite_por_hora_mostra_a_mensagem(self):
        for _ in range(3):
            self.pedir_link("ninguem@exemplo.com")

        resposta = self.pedir_link("ninguem@exemplo.com")

        self.assertContains(resposta, "Muitas solicitações. Tente novamente mais tarde")

    def test_fluxo_completo_tira_o_codigo_do_endereco_e_encerra_as_sessoes(self):
        outra_sessao = self.client_class()
        outra_sessao.force_login(self.aluno)
        self.pedir_link()
        codigo = codigo_do_email(mail.outbox[0])

        abrir = self.client.get(reverse("contas:redefinir_senha_link", args=[codigo]))
        self.assertRedirects(abrir, reverse("contas:redefinir_senha"), fetch_redirect_response=False)
        formulario = self.client.get(reverse("contas:redefinir_senha"))
        self.assertNotContains(formulario, codigo)

        resposta = self.client.post(
            reverse("contas:redefinir_senha"), {"nova_senha": NOVA_SENHA, "confirmacao": NOVA_SENHA}, follow=True
        )

        self.assertContains(resposta, "Senha alterada com sucesso")
        self.assertRedirects(outra_sessao.get(reverse("dicionario:busca")), f"{reverse('contas:entrar')}?next=/dicionario/")

    def test_senhas_diferentes_fracas_e_igual_a_atual_mostram_as_mensagens(self):
        self.pedir_link()
        self.client.get(reverse("contas:redefinir_senha_link", args=[codigo_do_email(mail.outbox[0])]))
        url = reverse("contas:redefinir_senha")

        diferentes = self.client.post(url, {"nova_senha": NOVA_SENHA, "confirmacao": "Outra123"})
        fraca = self.client.post(url, {"nova_senha": "12345678", "confirmacao": "12345678"})
        atual = self.client.post(url, {"nova_senha": SENHA, "confirmacao": SENHA})

        self.assertContains(diferentes, "As senhas informadas não coincidem")
        self.assertContains(fraca, "A senha deve ter ao menos 8 caracteres, com letras e números")
        self.assertContains(atual, "A nova senha deve ser diferente da senha atual")

    def test_link_invalido_mostra_a_mensagem(self):
        self.client.get(reverse("contas:redefinir_senha_link", args=["codigo-que-nao-existe"]))

        resposta = self.client.get(reverse("contas:redefinir_senha"))

        self.assertContains(resposta, "Link expirado ou inválido", status_code=400)
        self.assertContains(resposta, "Pedir um novo link", status_code=400)

    def test_login_tem_o_link_esqueci_minha_senha(self):
        self.assertContains(self.client.get(reverse("contas:entrar")), reverse("contas:esqueci_senha"))
