from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from contas.tests.fabricas import CPF_VALIDO_2, criar_admin, criar_aluno
from dicionario.exceptions import SinalNaoEncontrado
from dicionario.models import Favorito, Sinal
from dicionario.services import DicionarioService, FavoritoService

from .fabricas import MidiaTemporariaMixin, criar_categoria, criar_sinal


class FavoritoModeloTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        cls.sinal = criar_sinal("Mãe")

    def test_banco_recusa_o_mesmo_sinal_favoritado_duas_vezes(self):
        Favorito.objects.create(aluno=self.aluno, sinal=self.sinal)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorito.objects.create(aluno=self.aluno, sinal=self.sinal)

    def test_excluir_o_sinal_remove_os_favoritos(self):
        Favorito.objects.create(aluno=self.aluno, sinal=self.sinal)

        self.sinal.delete()

        self.assertFalse(Favorito.objects.exists())


class FavoritoServiceTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        cls.mae = criar_sinal("Mãe", categoria=criar_categoria("Família"))
        cls.pai = criar_sinal("Pai", categoria=criar_categoria("Pessoas"))

    def test_alternar_cria_e_depois_remove(self):
        self.assertTrue(FavoritoService.alternar(self.aluno, self.mae.pk))
        self.assertFalse(FavoritoService.alternar(self.aluno, self.mae.pk))
        self.assertFalse(Favorito.objects.exists())

    def test_alternar_recusa_sinal_inativo_ou_inexistente(self):
        Sinal.objects.filter(pk=self.pai.pk).update(ativo=False)

        for sinal_id in (self.pai.pk, 999999):
            with self.subTest(sinal_id=sinal_id), self.assertRaises(SinalNaoEncontrado):
                FavoritoService.alternar(self.aluno, sinal_id)

    def test_filtro_lista_so_os_favoritos_do_aluno_combinado_com_busca_e_categoria(self):
        outro = criar_aluno(email="joao@exemplo.com", cpf=CPF_VALIDO_2)
        Favorito.objects.create(aluno=self.aluno, sinal=self.mae)
        Favorito.objects.create(aluno=outro, sinal=self.pai)

        todos = DicionarioService.buscar(aluno=self.aluno, somente_favoritos=True)
        com_busca = DicionarioService.buscar(texto="pai", aluno=self.aluno, somente_favoritos=True)
        com_categoria = DicionarioService.buscar(
            categoria_id=self.mae.categoria_id, aluno=self.aluno, somente_favoritos=True
        )

        self.assertEqual(list(todos), [self.mae])
        self.assertEqual(list(com_busca), [])
        self.assertEqual(list(com_categoria), [self.mae])

    def test_sinal_inativado_some_dos_favoritos_e_volta_ao_ser_reativado(self):
        Favorito.objects.create(aluno=self.aluno, sinal=self.mae)

        Sinal.objects.filter(pk=self.mae.pk).update(ativo=False)
        self.assertEqual(list(DicionarioService.buscar(aluno=self.aluno, somente_favoritos=True)), [])

        Sinal.objects.filter(pk=self.mae.pk).update(ativo=True)
        self.assertEqual(
            list(DicionarioService.buscar(aluno=self.aluno, somente_favoritos=True)), [self.mae]
        )


class FavoritoViewTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        cls.mae = criar_sinal("Mãe")
        cls.url = reverse("dicionario:favoritar", args=[cls.mae.pk])
        cls.busca = reverse("dicionario:busca")

    def test_favoritar_e_remover_mostram_as_mensagens(self):
        self.client.force_login(self.aluno)

        adicionado = self.client.post(self.url, follow=True)
        removido = self.client.post(self.url, follow=True)

        self.assertContains(adicionado, "Sinal adicionado aos favoritos")
        self.assertContains(removido, "Sinal removido dos favoritos")

    def test_volta_para_a_pagina_de_origem_e_ignora_outro_dominio(self):
        self.client.force_login(self.aluno)

        local = self.client.post(self.url, {"proxima": f"{self.busca}?busca=mae"})
        externo = self.client.post(self.url, {"proxima": "https://exemplo.com/"})

        self.assertRedirects(local, f"{self.busca}?busca=mae", fetch_redirect_response=False)
        self.assertRedirects(externo, self.busca, fetch_redirect_response=False)

    def test_recusa_visitante_administrador_e_get(self):
        self.assertRedirects(
            self.client.post(self.url), f"{reverse('contas:entrar')}?next={self.url}"
        )

        self.client.force_login(self.aluno)
        self.assertEqual(self.client.get(self.url).status_code, 405)

        self.client.force_login(criar_admin())
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_filtro_sem_favoritos_mostra_a_mensagem(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.busca, {"favoritos": "on"})

        self.assertContains(resposta, "Você ainda não tem sinais favoritos")

    def test_filtro_com_busca_vazia_lista_os_favoritos_e_marca_o_botao(self):
        Favorito.objects.create(aluno=self.aluno, sinal=self.mae)
        self.client.force_login(self.aluno)

        resposta = self.client.get(self.busca, {"favoritos": "on"})

        self.assertContains(resposta, "<h2>Mãe</h2>", html=True)
        self.assertContains(resposta, "Remover dos favoritos")
        self.assertContains(resposta, 'aria-pressed="true"')

    def test_administrador_nao_ve_o_botao_nem_o_filtro(self):
        self.client.force_login(criar_admin())

        resposta = self.client.get(self.busca, {"busca": "mae"})

        self.assertContains(resposta, "<h2>Mãe</h2>", html=True)
        self.assertNotContains(resposta, "Favoritar")
        self.assertNotContains(resposta, "Somente favoritos")

    def test_numero_fixo_de_consultas_com_os_botoes(self):
        for termo in ("Pai", "Avó", "Irmão", "Tio"):
            sinal = criar_sinal(termo)
            Favorito.objects.create(aluno=self.aluno, sinal=sinal)
        self.client.force_login(self.aluno)
        self.client.get(self.busca, {"favoritos": "on"})

        # Sessão e usuário (2), categorias, contagem, página, ids dos favoritos e
        # existência de favoritos (5) e a sessão gravada com savepoint (3).
        with self.assertNumQueries(10):
            self.client.get(self.busca, {"favoritos": "on"})
