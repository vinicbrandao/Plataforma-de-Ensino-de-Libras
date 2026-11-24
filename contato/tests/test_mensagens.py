from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import CPF_VALIDO_2, criar_admin, criar_aluno
from contato.exceptions import LimiteDiarioAtingido, MensagemJaResolvida, RespostaObrigatoria
from contato.models import MensagemContato
from contato.services import MensagemService
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.tests.fabricas import criar_aula, criar_modulo

FUSO = ZoneInfo("America/Sao_Paulo")
TEXTO = "A legenda da aula está atrasada."


class ContatoMixin(MidiaTemporariaMixin):
    @classmethod
    def setUpTestData(cls):
        modulo = criar_modulo(1, "Alfabeto")
        cls.aula = criar_aula(modulo, 1, titulo="Letras A a E")
        cls.rascunho = criar_aula(modulo, 2, publicada=False, titulo="Rascunho")
        cls.aluno = criar_aluno()
        cls.outro = criar_aluno(email="joao@exemplo.com", cpf=CPF_VALIDO_2, nome_completo="João Souza")
        cls.admin = criar_admin()


class MensagemServiceTests(ContatoMixin, TestCase):
    def test_enviar_grava_aberta(self):
        mensagem = MensagemService.enviar(self.aluno, "DUVIDA", self.aula.pk, TEXTO)

        self.assertEqual(mensagem.situacao, "ABERTA")
        self.assertEqual(mensagem.aula, self.aula)

    def test_recusa_a_sexta_mensagem_do_dia_e_aceita_no_dia_seguinte(self):
        hoje = datetime(2026, 11, 24, 23, 30, tzinfo=FUSO)
        with mock.patch("django.utils.timezone.now", return_value=hoje):
            for _ in range(5):
                MensagemService.enviar(self.aluno, "SUGESTAO", None, TEXTO)
            with self.assertRaises(LimiteDiarioAtingido):
                MensagemService.enviar(self.aluno, "SUGESTAO", None, TEXTO)
        # 23h30 em Brasília já é outro dia em UTC; o limite usa o dia local.
        with mock.patch("django.utils.timezone.now", return_value=hoje + timedelta(hours=1)):
            MensagemService.enviar(self.aluno, "SUGESTAO", None, TEXTO)

    def test_aulas_disponiveis_so_publicadas_agrupadas_por_modulo(self):
        self.assertEqual(MensagemService.aulas_disponiveis(), [("Alfabeto", [(self.aula.pk, "Letras A a E")])])

    def test_atualizar_exige_resposta_para_resolvida_e_grava_a_data(self):
        mensagem = MensagemService.enviar(self.aluno, "DUVIDA", None, TEXTO)

        with self.assertRaises(RespostaObrigatoria):
            MensagemService.validar_atualizacao("ABERTA", "RESOLVIDA", "  ")

        mensagem.situacao, mensagem.resposta = "RESOLVIDA", "  Corrigimos.  "
        MensagemService.atualizar(mensagem, "ABERTA")
        mensagem.refresh_from_db()
        self.assertIsNotNone(mensagem.resolvida_em)
        self.assertEqual(mensagem.resposta, "Corrigimos.")

    def test_resolvida_nao_volta(self):
        with self.assertRaises(MensagemJaResolvida):
            MensagemService.validar_atualizacao("RESOLVIDA", "EM_ANALISE", "Resposta")

    def test_fila_poe_as_nao_resolvidas_mais_antigas_primeiro(self):
        base = datetime(2026, 11, 20, 10, tzinfo=FUSO)
        resolvida = MensagemContato.objects.create(
            aluno=self.aluno, assunto="DUVIDA", mensagem=TEXTO, enviada_em=base,
            situacao="RESOLVIDA", resposta="Ok, resolvido.", resolvida_em=base,
        )
        nova = MensagemContato.objects.create(
            aluno=self.aluno, assunto="DUVIDA", mensagem=TEXTO, enviada_em=base + timedelta(days=2)
        )
        antiga = MensagemContato.objects.create(
            aluno=self.outro, assunto="DUVIDA", mensagem=TEXTO, enviada_em=base + timedelta(days=1)
        )

        self.assertEqual(list(MensagemService.fila()), [antiga, nova, resolvida])


class FaleConoscoViewTests(ContatoMixin, TestCase):
    def test_envio_mostra_a_mensagem_e_leva_a_minhas_mensagens(self):
        self.client.force_login(self.aluno)

        resposta = self.client.post(
            reverse("contato:enviar"),
            {"assunto": "ERRO_CONTEUDO", "aula": self.aula.pk, "mensagem": TEXTO},
            follow=True,
        )

        self.assertRedirects(resposta, reverse("contato:minhas"))
        self.assertContains(resposta, "Mensagem enviada. Acompanhe a resposta em Minhas mensagens")
        self.assertContains(resposta, "Erro em conteúdo")

    def test_mensagem_curta_e_aula_nao_publicada_sao_recusadas(self):
        self.client.force_login(self.aluno)

        curta = self.client.post(reverse("contato:enviar"), {"assunto": "DUVIDA", "mensagem": "Oi"})
        rascunho = self.client.post(
            reverse("contato:enviar"), {"assunto": "DUVIDA", "aula": self.rascunho.pk, "mensagem": TEXTO}
        )

        self.assertContains(curta, "A mensagem deve ter entre 10 e 1.000 caracteres")
        self.assertTrue(rascunho.context["form"].errors["aula"])
        self.assertFalse(MensagemContato.objects.exists())

    def test_limite_diario_mantem_os_dados(self):
        for _ in range(5):
            MensagemService.enviar(self.aluno, "DUVIDA", None, TEXTO)
        self.client.force_login(self.aluno)

        resposta = self.client.post(reverse("contato:enviar"), {"assunto": "DUVIDA", "mensagem": "Sexta mensagem do dia"})

        self.assertContains(resposta, "Limite de 5 mensagens por dia atingido. Tente novamente amanhã")
        self.assertContains(resposta, "Sexta mensagem do dia")

    def test_minhas_mensagens_so_do_aluno_e_mensagem_vazia(self):
        self.client.force_login(self.aluno)
        self.assertContains(self.client.get(reverse("contato:minhas")), "Você ainda não enviou mensagens")

        MensagemService.enviar(self.outro, "DUVIDA", None, "Mensagem do João aqui")
        MensagemService.enviar(self.aluno, "DUVIDA", None, "<script>alert(1)</script>")
        resposta = self.client.get(reverse("contato:minhas"))

        self.assertNotContains(resposta, "Mensagem do João aqui")
        self.assertContains(resposta, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_recusa_visitante_e_administrador(self):
        url = reverse("contato:enviar")
        self.assertRedirects(self.client.get(url), f"{reverse('contas:entrar')}?next={url}")

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(reverse("contato:minhas")).status_code, 403)


class MensagemAdminTests(ContatoMixin, TestCase):
    def setUp(self):
        self.mensagem = MensagemService.enviar(self.aluno, "DUVIDA", None, TEXTO)
        self.url = reverse("admin:contato_mensagemcontato_change", args=[self.mensagem.pk])
        self.client.force_login(self.admin)

    def test_mostra_nome_e_email_sem_cpf_nem_deficiencia(self):
        resposta = self.client.get(self.url)

        self.assertContains(resposta, self.aluno.nome_completo)
        self.assertContains(resposta, self.aluno.email)
        self.assertNotContains(resposta, self.aluno.cpf)
        self.assertNotContains(resposta, "deficiência")

    def test_resolver_sem_resposta_mostra_erro(self):
        resposta = self.client.post(self.url, {"situacao": "RESOLVIDA", "resposta": ""})

        self.assertContains(resposta, "Informe a resposta para marcar como resolvida")

    def test_resolver_com_resposta_grava_a_data(self):
        self.client.post(self.url, {"situacao": "RESOLVIDA", "resposta": "Corrigimos a legenda."})

        self.mensagem.refresh_from_db()
        self.assertEqual(self.mensagem.situacao, "RESOLVIDA")
        self.assertIsNotNone(self.mensagem.resolvida_em)

    def test_nao_permite_incluir_nem_excluir(self):
        self.assertEqual(self.client.get(reverse("admin:contato_mensagemcontato_add")).status_code, 403)
        excluir = reverse("admin:contato_mensagemcontato_delete", args=[self.mensagem.pk])
        self.assertEqual(self.client.get(excluir).status_code, 403)
