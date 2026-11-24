from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import criar_aluno
from dicionario.models import Categoria
from dicionario.services import DicionarioService

from .fabricas import MidiaTemporariaMixin, criar_categoria, criar_sinal


class DicionarioServiceTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.familia = criar_categoria("Família")
        cls.cores = criar_categoria("Cores")
        cls.inativa = criar_categoria("Antiga", ativa=False)
        cls.mae = criar_sinal("Mãe", categoria=cls.familia)
        cls.azul = criar_sinal("Azul", categoria=cls.cores)
        cls.pai = criar_sinal("Pai", categoria=cls.familia, ativo=False)

    def _termos(self, **filtros) -> list[str]:
        return [sinal.termo for sinal in DicionarioService.buscar(**filtros)]

    def test_encontra_sem_acento_e_por_parte_do_termo(self):
        self.assertEqual(self._termos(texto="MAE"), ["Mãe"])
        self.assertEqual(self._termos(texto="zu"), ["Azul"])

    def test_ignora_sinais_inativos_e_ordena_por_termo(self):
        self.assertEqual(self._termos(), ["Azul", "Mãe"])

    def test_filtra_por_categoria_ativa(self):
        self.assertEqual(self._termos(categoria_id=self.familia.id), ["Mãe"])
        self.assertEqual(self._termos(categoria_id=self.inativa.id), [])

    def test_combina_texto_e_categoria(self):
        self.assertEqual(self._termos(texto="azul", categoria_id=self.familia.id), [])


class PaginacaoTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        for numero in range(21):
            criar_sinal(f"Sinal {numero:02d}")

    def test_pagina_com_20_sinais(self):
        primeira = DicionarioService.buscar()
        self.assertEqual(len(primeira), 20)
        self.assertEqual(primeira.paginator.num_pages, 2)

    def test_pagina_inexistente_vira_a_ultima(self):
        self.assertEqual(DicionarioService.buscar(pagina=99).number, 2)


class BuscaViewTests(MidiaTemporariaMixin, TestCase):
    url = reverse("dicionario:busca")

    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        criar_sinal("Mãe", categoria=criar_categoria("Família"))

    def test_visitante_e_redirecionado_para_o_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={self.url}")

    def test_aluno_ve_os_resultados(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.url, {"busca": "mae"})

        self.assertContains(resposta, "<h2>Mãe</h2>", html=True)
        self.assertContains(resposta, "Família")
        self.assertContains(resposta, "loop")

    def test_aluno_ve_mensagem_sem_resultados(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.url, {"busca": "zebra"})

        self.assertContains(
            resposta, "Nenhum sinal encontrado. Revise o termo ou escolha outra categoria"
        )

    def test_sem_busca_e_sem_categoria_nao_lista_sinais(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.url)

        self.assertIsNone(resposta.context["pagina"])
        self.assertNotContains(resposta, "<h2>Mãe</h2>", html=True)
        self.assertContains(resposta, "Digite uma palavra ou escolha uma categoria")

    def test_so_a_categoria_ja_lista_os_sinais(self):
        self.client.force_login(self.aluno)
        categoria = Categoria.objects.get(nome="Família")

        resposta = self.client.get(self.url, {"categoria": categoria.pk})

        self.assertContains(resposta, "<h2>Mãe</h2>", html=True)

    def test_busca_com_um_caractere_mostra_mensagem(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.url, {"busca": "m"})

        self.assertContains(resposta, "Digite ao menos 2 caracteres")
        self.assertNotContains(resposta, "<h2>Mãe</h2>", html=True)

    def test_menu_mostra_dicionario_so_para_autenticados(self):
        self.assertNotContains(self.client.get(reverse("inicio")), self.url)

        self.client.force_login(self.aluno)

        self.assertContains(self.client.get(reverse("inicio")), f'href="{self.url}"')
