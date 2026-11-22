from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.exceptions import CredenciaisInvalidas, LoginBloqueado, UsuarioDesativado
from contas.models import FalhaLogin
from contas.services import AutenticacaoService

from .fabricas import SENHA, criar_admin, criar_aluno


class AutenticacaoServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def test_aceita_email_com_maiusculas(self):
        self.assertEqual(AutenticacaoService.autenticar("MARIA@Exemplo.com", SENHA), self.aluno)

    def test_aceita_cpf_com_ou_sem_pontuacao(self):
        self.assertEqual(AutenticacaoService.autenticar("529.982.247-25", SENHA), self.aluno)
        self.assertEqual(AutenticacaoService.autenticar("52998224725", SENHA), self.aluno)

    def test_login_inexistente_e_senha_errada_levantam_a_mesma_excecao(self):
        with self.assertRaises(CredenciaisInvalidas):
            AutenticacaoService.autenticar("ninguem@exemplo.com", SENHA)
        with self.assertRaises(CredenciaisInvalidas):
            AutenticacaoService.autenticar("maria@exemplo.com", "errada123")

    def _falhar(self, login: str, vezes: int = 5) -> None:
        for _ in range(vezes):
            with self.assertRaises(CredenciaisInvalidas):
                AutenticacaoService.autenticar(login, "errada123")

    def test_sexta_tentativa_e_bloqueada_mesmo_com_a_senha_certa(self):
        self._falhar("maria@exemplo.com")

        with self.assertRaises(LoginBloqueado):
            AutenticacaoService.autenticar("maria@exemplo.com", SENHA)

    def test_bloqueio_vale_para_login_inexistente(self):
        self._falhar("ninguem@exemplo.com")

        with self.assertRaises(LoginBloqueado):
            AutenticacaoService.autenticar("ninguem@exemplo.com", "qualquer1")

    def test_bloqueio_vale_para_o_mesmo_cpf_com_ou_sem_pontuacao(self):
        self._falhar("52998224725")

        with self.assertRaises(LoginBloqueado):
            AutenticacaoService.autenticar("529.982.247-25", SENHA)

    def test_volta_a_aceitar_depois_de_15_minutos(self):
        self._falhar("maria@exemplo.com")
        depois = timezone.now() + timedelta(minutes=15, seconds=1)

        with mock.patch("contas.services.autenticacao.timezone.now", return_value=depois):
            self.assertEqual(AutenticacaoService.autenticar("maria@exemplo.com", SENHA), self.aluno)

    def test_login_bem_sucedido_zera_as_falhas(self):
        self._falhar("maria@exemplo.com", vezes=4)

        AutenticacaoService.autenticar("maria@exemplo.com", SENHA)

        self.assertFalse(FalhaLogin.objects.exists())
        self._falhar("maria@exemplo.com", vezes=4)  # Não bloqueia: o contador recomeçou.

    def test_nao_guarda_o_login_digitado(self):
        self._falhar("maria@exemplo.com", vezes=1)

        self.assertNotIn("maria", FalhaLogin.objects.get().chave)

    def test_inativo_com_senha_certa_recebe_usuario_desativado(self):
        self.aluno.is_active = False
        self.aluno.save()

        with self.assertRaises(UsuarioDesativado):
            AutenticacaoService.autenticar("maria@exemplo.com", SENHA)
        with self.assertRaises(CredenciaisInvalidas):
            AutenticacaoService.autenticar("maria@exemplo.com", "errada123")


class EntrarViewTests(TestCase):
    url = reverse("contas:entrar")

    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def test_login_valido_redireciona_para_inicio(self):
        resposta = self.client.post(self.url, {"login": "maria@exemplo.com", "senha": SENHA})

        self.assertRedirects(resposta, reverse("inicio"))

    def test_senha_errada_mostra_mensagem_generica(self):
        resposta = self.client.post(self.url, {"login": "maria@exemplo.com", "senha": "x"})

        self.assertContains(resposta, "Login ou senha inválidos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_campos_vazios_mostram_obrigatorio(self):
        resposta = self.client.post(self.url, {"login": "", "senha": ""})

        self.assertContains(resposta, "Campo obrigatório não preenchido")

    def test_bloqueio_mostra_mensagem(self):
        for _ in range(5):
            self.client.post(self.url, {"login": "maria@exemplo.com", "senha": "x"})

        resposta = self.client.post(self.url, {"login": "maria@exemplo.com", "senha": SENHA})

        self.assertContains(resposta, "Muitas tentativas de acesso. Tente novamente em 15 minutos")

    def test_inativo_ve_usuario_desativado(self):
        self.aluno.is_active = False
        self.aluno.save()

        resposta = self.client.post(self.url, {"login": "maria@exemplo.com", "senha": SENHA})

        self.assertContains(resposta, "Usuário desativado")

    def test_next_interno_e_respeitado(self):
        resposta = self.client.post(
            self.url, {"login": "maria@exemplo.com", "senha": SENHA, "next": "/cadastro/"}
        )

        self.assertEqual(resposta["Location"], "/cadastro/")

    def test_next_externo_e_ignorado(self):
        resposta = self.client.post(
            self.url,
            {"login": "maria@exemplo.com", "senha": SENHA, "next": "https://exemplo.com/"},
        )

        self.assertRedirects(resposta, reverse("inicio"))

    def test_administrador_vai_para_o_admin(self):
        criar_admin()

        resposta = self.client.post(self.url, {"login": "admin@exemplo.com", "senha": SENHA})

        self.assertRedirects(resposta, reverse("admin:index"))

    def test_usuario_autenticado_e_redirecionado(self):
        self.client.force_login(self.aluno)

        self.assertRedirects(self.client.get(self.url), reverse("inicio"))

    def test_login_do_admin_tambem_usa_o_bloqueio(self):
        criar_admin()
        url_admin = reverse("admin:login")
        for _ in range(5):
            self.client.post(url_admin, {"username": "admin@exemplo.com", "password": "x"})

        self.client.post(url_admin, {"username": "admin@exemplo.com", "password": SENHA})

        self.assertNotIn("_auth_user_id", self.client.session)


class SessaoTests(TestCase):
    def test_tela_restrita_sem_autenticacao_redireciona_para_o_login(self):
        resposta = self.client.get(reverse("admin:index"))

        self.assertEqual(resposta.status_code, 302)

    def test_sair_por_post_encerra_a_sessao(self):
        self.client.force_login(criar_aluno())

        resposta = self.client.post(reverse("contas:sair"))

        self.assertRedirects(resposta, reverse("contas:entrar"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sair_por_get_devolve_405(self):
        self.client.force_login(criar_aluno())

        self.assertEqual(self.client.get(reverse("contas:sair")).status_code, 405)

    def test_respostas_para_autenticados_nao_vao_para_o_cache(self):
        self.client.force_login(criar_aluno())

        resposta = self.client.get(reverse("inicio"))

        self.assertIn("no-store", resposta["Cache-Control"])

    def test_respostas_para_visitantes_podem_ir_para_o_cache(self):
        resposta = self.client.get(reverse("inicio"))

        self.assertNotIn("no-store", resposta.get("Cache-Control", ""))

    def test_sessao_expira_apos_30_minutos_de_inatividade(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 30 * 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
