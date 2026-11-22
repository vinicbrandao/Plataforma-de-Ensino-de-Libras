from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario
from contas.tests.fabricas import criar_admin, criar_aluno
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.models import ProgressoAula
from trilha.services import ProgressoService, TrilhaService

from .fabricas import criar_aula, criar_modulo


class TrilhaComConteudoMixin(MidiaTemporariaMixin):
    @classmethod
    def setUpTestData(cls):
        cls.m1 = criar_modulo(1)
        cls.m2 = criar_modulo(2)
        cls.m3 = criar_modulo(3)
        criar_modulo(4)  # Sem aulas publicadas.
        cls.a11 = criar_aula(cls.m1, 1)
        cls.a12 = criar_aula(cls.m1, 2)
        cls.a13_rascunho = criar_aula(cls.m1, 3, publicada=False)
        cls.a21 = criar_aula(cls.m2, 1)
        cls.a31 = criar_aula(cls.m3, 1)
        cls.aluno = criar_aluno()


class TrilhaServiceTests(TrilhaComConteudoMixin, TestCase):
    def test_mostra_so_aulas_publicadas_e_oculta_modulos_vazios(self):
        trilha = TrilhaService.montar(AnonymousUser())

        self.assertEqual([m.modulo for m in trilha.modulos], [self.m1, self.m2, self.m3])
        self.assertEqual([a.aula for a in trilha.modulos[0].aulas], [self.a11, self.a12])

    def test_visitante_so_tem_a_primeira_aula_liberada(self):
        trilha = TrilhaService.montar(AnonymousUser())

        liberadas = [a.aula for m in trilha.modulos for a in m.aulas if a.liberada]
        self.assertEqual(liberadas, [self.a11])

    def test_aluno_ve_status_e_percentuais(self):
        ProgressoService.concluir(self.aluno, self.a11)
        ProgressoService.registrar_acesso(self.aluno, self.a12)

        trilha = TrilhaService.montar(self.aluno)

        primeiro = trilha.modulos[0]
        self.assertEqual([a.status for a in primeiro.aulas], ["CONCLUIDA", "EM_ANDAMENTO"])
        self.assertEqual((primeiro.concluidas, primeiro.publicadas, primeiro.percentual), (1, 2, 50))
        self.assertEqual((trilha.concluidas, trilha.publicadas, trilha.percentual), (1, 4, 25))

    def test_recomendacao_segue_o_contato_com_libras(self):
        casos = {"NUNCA": 1, "POUCOS_SINAIS": 1, "BASICO": 2, "EXPERIENTE": 3}
        for resposta, ordem in casos.items():
            with self.subTest(resposta=resposta):
                Usuario.objects.filter(pk=self.aluno.pk).update(contato_libras=resposta)
                self.aluno.refresh_from_db()
                trilha = TrilhaService.montar(self.aluno)
                self.assertEqual(trilha.ordem_recomendada, ordem)
                self.assertTrue(trilha.modulos[ordem - 1].recomendado)

    def test_continuar_prefere_a_aula_em_andamento_mais_recente(self):
        ProgressoService.registrar_acesso(self.aluno, self.a21)
        ProgressoService.registrar_acesso(self.aluno, self.a12)

        self.assertEqual(TrilhaService.montar(self.aluno).continuar, self.a12)

    def test_continuar_sem_andamento_vai_ao_modulo_recomendado(self):
        Usuario.objects.filter(pk=self.aluno.pk).update(contato_libras="BASICO")
        self.aluno.refresh_from_db()

        self.assertEqual(TrilhaService.montar(self.aluno).continuar, self.a21)

    def test_continuar_pula_aulas_concluidas(self):
        ProgressoService.concluir(self.aluno, self.a11)

        self.assertEqual(TrilhaService.montar(self.aluno).continuar, self.a12)

    def test_montar_usa_numero_fixo_de_consultas(self):
        with self.assertNumQueries(4):
            TrilhaService.montar(self.aluno)
        with self.assertNumQueries(2):
            TrilhaService.montar(AnonymousUser())


class TrilhaViewTests(TrilhaComConteudoMixin, TestCase):
    def test_visitante_ve_a_trilha_com_aulas_bloqueadas(self):
        resposta = self.client.get(reverse("inicio"))

        self.assertContains(resposta, "Módulo 1: Módulo 1")
        self.assertContains(resposta, "aula gratuita")
        self.assertContains(resposta, "faça login")
        self.assertNotContains(resposta, "Aula 1.3")

    def test_aluno_ve_progresso_recomendacao_e_continuar(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("inicio"))

        self.assertContains(resposta, "Comece pelo Módulo 1!")
        self.assertContains(resposta, "0 de 4 aulas · 0%")
        self.assertContains(resposta, "Continuar: Aula 1.1")
        self.assertContains(resposta, "Não iniciada")


class AulaViewTests(TrilhaComConteudoMixin, TestCase):
    def test_visitante_abre_a_primeira_aula_sem_registro(self):
        resposta = self.client.get(reverse("trilha:aula", args=[self.a11.pk]))

        self.assertContains(resposta, "Faça login para salvar seu progresso")
        self.assertContains(resposta, '<track kind="subtitles"')
        self.assertFalse(ProgressoAula.objects.exists())

    def test_visitante_e_redirecionado_nas_outras_aulas(self):
        url = reverse("trilha:aula", args=[self.a12.pk])

        resposta = self.client.get(url, follow=True)

        self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={url}")
        self.assertContains(resposta, "Faça login para acessar esta aula")

    def test_aluno_abre_qualquer_aula_e_registra_em_andamento(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("trilha:aula", args=[self.a31.pk]))

        self.assertContains(resposta, "Em andamento")
        self.assertEqual(ProgressoAula.objects.get().aula, self.a31)

    def test_legenda_comeca_ativada_para_deficiencia_auditiva(self):
        Usuario.objects.filter(pk=self.aluno.pk).update(deficiencia="AUDITIVA")
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("trilha:aula", args=[self.a11.pk]))

        self.assertRegex(resposta.content.decode(), r"<track [^>]*default>")

    def test_legenda_comeca_desativada_para_os_demais(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("trilha:aula", args=[self.a11.pk]))

        self.assertNotRegex(resposta.content.decode(), r"<track [^>]*default>")

    def test_aula_concluida_mostra_mensagem_e_proxima(self):
        ProgressoService.concluir(self.aluno, self.a12)
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("trilha:aula", args=[self.a12.pk]))

        self.assertContains(resposta, "Aula concluída!")
        self.assertContains(resposta, "Próxima aula: Aula 2.1")

    def test_aula_nao_publicada_da_404_ao_aluno_e_abre_para_o_admin(self):
        url = reverse("trilha:aula", args=[self.a13_rascunho.pk])
        self.client.force_login(self.aluno)
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(criar_admin())

        resposta = self.client.get(url)
        self.assertContains(resposta, "Pré-visualização")
        self.assertFalse(ProgressoAula.objects.exists())

    def test_aula_inexistente_da_404(self):
        self.assertEqual(self.client.get(reverse("trilha:aula", args=[999999])).status_code, 404)
