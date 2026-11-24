import re
import shutil
import tempfile
from datetime import date, timedelta
from unittest import mock

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contas.exceptions import EmailJaCadastrado, LinkConfirmacaoInvalido, SenhaAtualIncorreta, SenhaIgualAAtual
from contas.models import HistoricoAlteracao, Usuario
from contas.services import DadosPerfil, PerfilService
from trilha.services import TrilhaService
from trilha.tests.fabricas import criar_aula, criar_modulo

from .fabricas import CPF_VALIDO, CPF_VALIDO_2, SENHA, criar_admin, criar_aluno

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
NOVA_SENHA = "OutraSenha456"


def dados(aluno, **alteracoes) -> DadosPerfil:
    valores = {
        "nome_completo": aluno.nome_completo,
        "email": aluno.email,
        "telefone": aluno.telefone,
        "deficiencia": aluno.deficiencia,
        "qual_deficiencia": aluno.qual_deficiencia,
        "contato_libras": aluno.contato_libras,
        "receber_lembretes": aluno.receber_lembretes,
    }
    valores.update(alteracoes)
    return DadosPerfil(**valores)


def montar_link(codigo: str) -> str:
    return f"http://testserver{reverse('contas:confirmar_email', args=[codigo])}"


def codigo_do_email(mensagem) -> str:
    return re.search(r"/perfil/confirmar-email/([^/\s]+)/", mensagem.body).group(1)


class MidiaTemporariaMixin:
    @classmethod
    def setUpClass(cls):
        cls._pasta = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._pasta)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._pasta, ignore_errors=True)


class AtualizarTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def test_cada_campo_alterado_gera_uma_linha_de_historico(self):
        PerfilService.atualizar(
            self.aluno, dados(self.aluno, telefone="(11) 98888-7777", receber_lembretes=False), montar_link
        )

        linhas = {h.campo: (h.valor_anterior, h.valor_novo) for h in HistoricoAlteracao.objects.all()}
        self.assertEqual(linhas, {
            "telefone": ("(11) 91234-5678", "(11) 98888-7777"),
            "receber_lembretes": ("Sim", "Não"),
        })
        self.aluno.refresh_from_db()
        self.assertFalse(self.aluno.receber_lembretes)

    def test_sem_alteracao_nao_grava_historico(self):
        PerfilService.atualizar(self.aluno, dados(self.aluno), montar_link)

        self.assertFalse(HistoricoAlteracao.objects.exists())

    def test_email_novo_so_vale_depois_da_confirmacao_e_avisa_o_anterior(self):
        with self.captureOnCommitCallbacks(execute=True):
            pendente = PerfilService.atualizar(self.aluno, dados(self.aluno, email="nova@exemplo.com"), montar_link)

        self.assertTrue(pendente)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.email, "maria@exemplo.com")
        self.assertEqual(mail.outbox[0].to, ["nova@exemplo.com"])

        with self.captureOnCommitCallbacks(execute=True):
            PerfilService.confirmar_email(codigo_do_email(mail.outbox[0]))

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.email, "nova@exemplo.com")
        self.assertEqual(mail.outbox[-1].to, ["maria@exemplo.com"])
        self.assertTrue(HistoricoAlteracao.objects.filter(campo="email", valor_novo="nova@exemplo.com").exists())

    def test_link_de_confirmacao_vence_em_24_horas_e_vale_uma_vez(self):
        with self.captureOnCommitCallbacks(execute=True):
            PerfilService.atualizar(self.aluno, dados(self.aluno, email="nova@exemplo.com"), montar_link)
        codigo = codigo_do_email(mail.outbox[0])

        with mock.patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(hours=25)):
            with self.assertRaises(LinkConfirmacaoInvalido):
                PerfilService.confirmar_email(codigo)
        PerfilService.confirmar_email(codigo)
        with self.assertRaises(LinkConfirmacaoInvalido):
            PerfilService.confirmar_email(codigo)

    def test_email_ja_usado_e_recusado_ao_pedir_e_ao_confirmar(self):
        outro = criar_aluno(email="joao@exemplo.com", cpf=CPF_VALIDO_2, nome_completo="João Souza")
        with self.assertRaises(EmailJaCadastrado):
            PerfilService.atualizar(self.aluno, dados(self.aluno, email="joao@exemplo.com"), montar_link)

        with self.captureOnCommitCallbacks(execute=True):
            PerfilService.atualizar(self.aluno, dados(self.aluno, email="livre@exemplo.com"), montar_link)
        Usuario.objects.filter(pk=outro.pk).update(email="livre@exemplo.com")
        with self.assertRaises(EmailJaCadastrado):
            PerfilService.confirmar_email(codigo_do_email(mail.outbox[0]))

    def test_alterar_contato_com_libras_muda_o_modulo_recomendado(self):
        modulos = [criar_modulo(posicao) for posicao in (1, 2, 3)]
        for modulo in modulos:
            criar_aula(modulo, 1)

        PerfilService.atualizar(self.aluno, dados(self.aluno, contato_libras="EXPERIENTE"), montar_link)

        self.aluno.refresh_from_db()
        trilha = TrilhaService.montar(self.aluno)
        self.assertEqual(trilha.ordem_recomendada, 3)


class TrocarSenhaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def test_exige_a_senha_atual_e_recusa_a_mesma(self):
        with self.assertRaises(SenhaAtualIncorreta):
            PerfilService.trocar_senha(self.aluno, "errada123", NOVA_SENHA)
        with self.assertRaises(SenhaIgualAAtual):
            PerfilService.trocar_senha(self.aluno, SENHA, SENHA)

    def test_troca_e_registra_so_a_data(self):
        PerfilService.trocar_senha(self.aluno, SENHA, NOVA_SENHA)

        self.assertTrue(self.aluno.check_password(NOVA_SENHA))
        linha = HistoricoAlteracao.objects.get()
        self.assertEqual((linha.campo, linha.valor_anterior, linha.valor_novo), ("senha", "", ""))


class PerfilViewTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def setUp(self):
        self.client.force_login(self.aluno)

    def form(self, **alteracoes) -> dict:
        valores = {
            "nome_completo": "Maria da Silva",
            "email": "maria@exemplo.com",
            "telefone": "11912345678",
            "deficiencia": "NAO",
            "qual_deficiencia": "",
            "contato_libras": "NUNCA",
            "receber_lembretes": "on",
        }
        valores.update(alteracoes)
        return valores

    def test_mostra_cpf_e_nascimento_so_para_leitura(self):
        resposta = self.client.get(reverse("contas:perfil"))

        self.assertContains(resposta, CPF_VALIDO)
        self.assertContains(resposta, "10/05/1995")
        self.assertNotContains(resposta, 'name="cpf"')
        self.assertNotContains(resposta, 'name="data_nascimento"')

    def test_post_nao_altera_cpf_nem_nascimento(self):
        resposta = self.client.post(
            reverse("contas:perfil"),
            self.form(nome_completo="Maria Souza", cpf="111.444.777-35", data_nascimento="2000-01-01"),
            follow=True,
        )

        self.assertContains(resposta, "Dados atualizados com sucesso")
        self.aluno.refresh_from_db()
        self.assertEqual((self.aluno.nome_completo, self.aluno.cpf, self.aluno.data_nascimento),
                         ("Maria Souza", CPF_VALIDO, date(1995, 5, 10)))

    def test_email_novo_mostra_a_mensagem_de_confirmacao(self):
        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(reverse("contas:perfil"), self.form(email="Nova@Exemplo.com"), follow=True)

        self.assertContains(resposta, "Enviamos um link de confirmação para o novo e-mail")
        self.assertEqual(mail.outbox[0].to, ["nova@exemplo.com"])

    def test_erros_aparecem_sem_apagar_o_digitado(self):
        resposta = self.client.post(reverse("contas:perfil"), self.form(telefone="123", nome_completo="Maria 2"))

        self.assertContains(resposta, "Telefone inválido")
        self.assertContains(resposta, "Nome inválido")
        self.assertContains(resposta, 'value="123"')

    def test_foto_aceita_jpg_e_png_e_apaga_a_anterior(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("contas:foto"), {"foto": SimpleUploadedFile("eu.png", PNG)})
        self.aluno.refresh_from_db()
        primeira = self.aluno.foto.name
        self.assertRegex(primeira, r"^perfis/[0-9a-f]{32}\.png$")

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("contas:foto"), {"foto": SimpleUploadedFile("eu.jpeg", JPG)})
        self.aluno.refresh_from_db()
        self.assertRegex(self.aluno.foto.name, r"^perfis/[0-9a-f]{32}\.jpg$")
        self.assertFalse(self.aluno.foto.storage.exists(primeira))

    def test_foto_invalida_mostra_a_mensagem(self):
        falsa = SimpleUploadedFile("eu.png", b"%PDF-1.7 nao e imagem")
        grande = SimpleUploadedFile("eu.png", PNG + b"\x00" * (2 * 1024 * 1024))

        for arquivo in (falsa, grande):
            resposta = self.client.post(reverse("contas:foto"), {"foto": arquivo})
            self.assertContains(resposta, "Arquivo inválido. Envie uma imagem JPG ou PNG de até 2 MB")

    def test_troca_de_senha_mantem_a_sessao(self):
        resposta = self.client.post(
            reverse("contas:trocar_senha"),
            {"senha_atual": SENHA, "nova_senha": NOVA_SENHA, "confirmacao": NOVA_SENHA},
            follow=True,
        )

        self.assertContains(resposta, "Senha alterada com sucesso")
        self.assertEqual(self.client.get(reverse("contas:perfil")).status_code, 200)

    def test_troca_de_senha_mostra_as_mensagens(self):
        url = reverse("contas:trocar_senha")

        errada = self.client.post(url, {"senha_atual": "errada123", "nova_senha": NOVA_SENHA, "confirmacao": NOVA_SENHA})
        igual = self.client.post(url, {"senha_atual": SENHA, "nova_senha": SENHA, "confirmacao": SENHA})

        self.assertContains(errada, "Senha atual incorreta")
        self.assertContains(igual, "A nova senha deve ser diferente da senha atual")

    def test_link_de_confirmacao_invalido_mostra_a_mensagem(self):
        resposta = self.client.get(reverse("contas:confirmar_email", args=["nao-existe"]))

        self.assertContains(resposta, "Link de confirmação expirado ou inválido", status_code=400)

    def test_rotas_recusam_visitante_e_administrador(self):
        url = reverse("contas:perfil")
        self.client.logout()
        self.assertRedirects(self.client.get(url), f"{reverse('contas:entrar')}?next={url}")

        self.client.force_login(criar_admin())
        for nome in ("contas:perfil", "contas:trocar_senha"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 403)

    def test_menu_mostra_perfil_ao_aluno(self):
        self.assertContains(self.client.get(reverse("inicio")), f'href="{reverse("contas:perfil")}"')
