from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import criar_admin
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.models import Aula, Modulo

from .fabricas import criar_aula, criar_modulo, legenda, video


class TrilhaAdminTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = criar_admin()
        cls.modulo = criar_modulo(1, "Primeiros sinais")

    def setUp(self):
        self.client.force_login(self.admin)

    def _dados_aula(self, **alteracoes) -> dict:
        dados = {
            "modulo": self.modulo.pk, "titulo": "Alfabeto", "descricao": "D", "posicao": 1,
            "texto_apoio": "", "materiais-TOTAL_FORMS": 0, "materiais-INITIAL_FORMS": 0,
        }
        dados.update(alteracoes)
        return dados

    def test_modulo_com_titulo_e_posicao_repetidos_mostra_mensagens(self):
        resposta = self.client.post(
            reverse("admin:trilha_modulo_add"),
            {"titulo": "PRIMEIROS SINAIS", "descricao": "D", "posicao": 1},
        )

        self.assertContains(resposta, "Título já cadastrado")
        self.assertContains(resposta, "Posição já cadastrada")
        self.assertEqual(Modulo.objects.count(), 1)

    def test_publicacao_incompleta_mostra_mensagem(self):
        resposta = self.client.post(reverse("admin:trilha_aula_add"), self._dados_aula(publicada="on"))

        self.assertContains(resposta, "A aula precisa de vídeo, legenda e questões para ser publicada")
        self.assertFalse(Aula.objects.exists())

    def test_aula_nova_com_video_e_legenda_nao_publica_sem_questao(self):
        resposta = self.client.post(
            reverse("admin:trilha_aula_add"),
            self._dados_aula(publicada="on", video=video(), legenda=legenda()),
        )

        self.assertContains(resposta, "A aula precisa de vídeo, legenda e questões para ser publicada")
        self.assertFalse(Aula.objects.exists())

    def test_cria_aula_nao_publicada_com_video_e_legenda(self):
        resposta = self.client.post(
            reverse("admin:trilha_aula_add"), self._dados_aula(video=video(), legenda=legenda())
        )

        self.assertRedirects(resposta, reverse("admin:trilha_aula_changelist"))
        self.assertFalse(Aula.objects.get().publicada)

    def test_titulo_de_aula_repetido_no_modulo_mostra_mensagem(self):
        criar_aula(self.modulo, 1, titulo="Alfabeto")

        resposta = self.client.post(reverse("admin:trilha_aula_add"), self._dados_aula(posicao=2))

        self.assertContains(resposta, "Título já cadastrado")

    def test_ver_no_site_leva_a_tela_da_aula(self):
        aula = criar_aula(self.modulo, 1, publicada=False)

        resposta = self.client.get(reverse("admin:trilha_aula_change", args=[aula.pk]))

        self.assertContains(resposta, reverse("trilha:aula", args=[aula.pk]))
