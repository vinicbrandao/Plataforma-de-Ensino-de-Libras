from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import criar_admin
from dicionario.models import Categoria, Sinal

from .fabricas import MidiaTemporariaMixin, criar_categoria, criar_sinal, video_mp4


class SinalAdminTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = criar_admin()

    def setUp(self):
        self.client.force_login(self.admin)

    def _criar(self, termo: str):
        dados = {"termo": termo, "classe_gramatical": "", "categoria": "",
                 "descricao_execucao": "", "video": video_mp4(), "ativo": "on"}
        return self.client.post(reverse("admin:dicionario_sinal_add"), dados)

    def test_cria_sinal_com_nome_de_arquivo_gerado(self):
        resposta = self._criar("Obrigado")

        self.assertRedirects(resposta, reverse("admin:dicionario_sinal_changelist"))
        sinal = Sinal.objects.get()
        self.assertEqual(sinal.termo_normalizado, "obrigado")
        self.assertNotIn("sinal.mp4", sinal.video.name)

    def test_recusa_termo_repetido_com_mensagem_no_campo(self):
        criar_sinal("Mãe")

        resposta = self._criar("MAE")

        self.assertContains(resposta, "Termo já cadastrado")
        self.assertEqual(Sinal.objects.count(), 1)

    def test_pesquisa_encontra_sinal_sem_acento(self):
        criar_sinal("Mãe")
        criar_sinal("Azul")

        resposta = self.client.get(reverse("admin:dicionario_sinal_changelist"), {"q": "mae"})

        self.assertContains(resposta, "Mãe")
        self.assertNotContains(resposta, "Azul")


class CategoriaAdminTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = criar_admin()

    def setUp(self):
        self.client.force_login(self.admin)
        self.categoria = criar_categoria("Família")
        criar_sinal(categoria=self.categoria)

    def test_recusa_inativar_categoria_com_sinais_ativos(self):
        url = reverse("admin:dicionario_categoria_change", args=[self.categoria.pk])

        resposta = self.client.post(url, {"nome": "Família"})  # ativa desmarcada

        self.assertContains(resposta, "Existem sinais ativos nesta categoria")
        self.categoria.refresh_from_db()
        self.assertTrue(self.categoria.ativa)

    def test_recusa_categoria_repetida(self):
        resposta = self.client.post(
            reverse("admin:dicionario_categoria_add"), {"nome": "familia", "ativa": "on"}
        )

        self.assertContains(resposta, "Categoria já cadastrada")

    def test_nao_exclui_categoria_com_sinais(self):
        url = reverse("admin:dicionario_categoria_delete", args=[self.categoria.pk])

        self.client.post(url, {"post": "yes"})

        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
