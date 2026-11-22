from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from contas.tests.fabricas import criar_admin, criar_aluno
from dicionario.tests.fabricas import MidiaTemporariaMixin
from questionarios.exceptions import RespostasIncompletas
from questionarios.models import Alternativa, Questao, Tentativa
from questionarios.services import QuestionarioService
from trilha.models import ProgressoAula
from trilha.services import ProgressoService, TrilhaService
from trilha.tests.fabricas import criar_aula, criar_modulo

from .fabricas import criar_questao, respostas


class AprovacaoTests(SimpleTestCase):
    def test_setenta_por_cento_aprova_sem_arredondar(self):
        self.assertTrue(QuestionarioService.aprovado(7, 10))
        self.assertFalse(QuestionarioService.aprovado(2, 3))
        self.assertFalse(QuestionarioService.aprovado(6, 10))
        self.assertTrue(QuestionarioService.aprovado(3, 3))


class QuestionarioComAulasMixin(MidiaTemporariaMixin):
    @classmethod
    def setUpTestData(cls):
        modulo = criar_modulo(1)
        cls.aula = criar_aula(modulo, 1)
        cls.segunda = criar_aula(modulo, 2)
        cls.questoes = [criar_questao(cls.aula, posicao) for posicao in (1, 2, 3)]
        criar_questao(cls.segunda, 1)
        cls.aluno = criar_aluno()


class CorrigirTests(QuestionarioComAulasMixin, TestCase):
    def test_recusa_respostas_incompletas(self):
        incompletas = respostas(self.questoes, 3)
        incompletas.pop(self.questoes[2].pk)

        with self.assertRaises(RespostasIncompletas):
            QuestionarioService.corrigir(self.aula.pk, self.aluno, incompletas)

    def test_recusa_alternativa_de_outra_questao(self):
        trocadas = respostas(self.questoes, 3)
        trocadas[self.questoes[0].pk] = self.questoes[1].alternativas.first().pk

        with self.assertRaises(RespostasIncompletas):
            QuestionarioService.corrigir(self.aula.pk, self.aluno, trocadas)

    def test_aluno_aprovado_grava_tentativa_e_conclui_a_aula(self):
        resultado = QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 3))

        self.assertTrue(resultado.aprovado)
        self.assertTrue(resultado.aula_concluida)
        self.assertEqual(resultado.proxima, self.segunda)
        tentativa = Tentativa.objects.get()
        self.assertEqual((tentativa.acertos, tentativa.total, tentativa.percentual), (3, 3, 100))
        self.assertEqual(ProgressoAula.objects.get().status, ProgressoAula.Status.CONCLUIDA)

    def test_aluno_reprovado_so_grava_a_tentativa(self):
        resultado = QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 2))

        self.assertFalse(resultado.aprovado)
        self.assertEqual(resultado.percentual, 67)
        self.assertFalse(Tentativa.objects.get().aprovada)
        self.assertFalse(ProgressoAula.objects.exists())

    def test_reprovar_depois_de_aprovado_nao_desfaz_a_conclusao(self):
        QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 3))

        QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 0))

        self.assertEqual(ProgressoAula.objects.get().status, ProgressoAula.Status.CONCLUIDA)
        self.assertEqual(Tentativa.objects.count(), 2)

    def test_visitante_e_administrador_nao_gravam_nada(self):
        QuestionarioService.corrigir(self.aula.pk, AnonymousUser(), respostas(self.questoes, 3))
        QuestionarioService.corrigir(self.aula.pk, criar_admin(), respostas(self.questoes, 3))

        self.assertFalse(Tentativa.objects.exists())
        self.assertFalse(ProgressoAula.objects.exists())

    def test_alterar_ou_excluir_questao_nao_muda_tentativas(self):
        QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 2))
        Questao.objects.filter(pk=self.questoes[0].pk).update(enunciado="Mudou")
        Alternativa.objects.filter(questao=self.questoes[2]).delete()
        Questao.objects.filter(pk=self.questoes[2].pk).delete()

        tentativa = Tentativa.objects.get()
        self.assertEqual((tentativa.acertos, tentativa.total), (2, 3))

    def test_aprovacao_atualiza_a_trilha(self):
        QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 3))

        trilha = TrilhaService.montar(self.aluno)

        self.assertEqual(trilha.modulos[0].aulas[0].status, "CONCLUIDA")
        self.assertEqual(trilha.modulos[0].percentual, 50)


class QuestionarioViewTests(QuestionarioComAulasMixin, TestCase):
    def _url(self, aula=None) -> str:
        return reverse("questionarios:responder", args=[(aula or self.aula).pk])

    def _dados(self, acertos: int) -> dict:
        return {f"questao_{q}": a for q, a in respostas(self.questoes, acertos).items()}

    def test_aluno_aprovado_ve_mensagem_e_aula_concluida(self):
        self.client.force_login(self.aluno)

        resposta = self.client.post(self._url(), self._dados(3))

        self.assertContains(resposta, "Aprovado! Você acertou 3 de 3 questões")
        self.assertContains(resposta, "Aula concluída!")
        self.assertContains(resposta, "Próxima aula: Aula 1.2")

    def test_aluno_reprovado_ve_mensagem_e_correcao(self):
        self.client.force_login(self.aluno)

        resposta = self.client.post(self._url(), self._dados(2))

        self.assertContains(
            resposta, "Você acertou 2 de 3 questões. É necessário acertar 70% para concluir. Tente novamente"
        )
        self.assertContains(resposta, "Alternativa correta: <strong>Q3 opção 1</strong>", html=True)

    def test_respostas_incompletas_mantem_as_marcadas(self):
        self.client.force_login(self.aluno)
        dados = self._dados(3)
        dados.pop(f"questao_{self.questoes[2].pk}")

        resposta = self.client.post(self._url(), dados)

        self.assertContains(resposta, "Responda todas as questões antes de enviar")
        marcada = dados[f"questao_{self.questoes[0].pk}"]
        self.assertRegex(resposta.content.decode(), rf'value="{marcada}"[^>]*checked')
        self.assertFalse(Tentativa.objects.exists())

    def test_visitante_responde_a_primeira_aula_sem_registro(self):
        resposta = self.client.post(self._url(), self._dados(3))

        self.assertContains(resposta, "Aprovado!")
        self.assertContains(resposta, "Faça login para salvar seu progresso")
        self.assertFalse(Tentativa.objects.exists())

    def test_visitante_e_redirecionado_nas_outras_aulas(self):
        url = self._url(self.segunda)

        resposta = self.client.get(url)

        self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={url}", fetch_redirect_response=False)

    def test_tela_da_aula_tem_o_botao_do_questionario(self):
        self.client.force_login(self.aluno)
        ProgressoService.registrar_acesso(self.aluno, self.aula)

        resposta = self.client.get(reverse("trilha:aula", args=[self.aula.pk]))

        self.assertContains(resposta, f'href="{self._url()}"')


class AdminQuestoesTests(QuestionarioComAulasMixin, TestCase):
    def setUp(self):
        self.client.force_login(criar_admin())

    def _dados(self, aula, posicao, corretas) -> dict:
        dados = {
            "aula": aula.pk, "enunciado": "Qual é o sinal?", "sinal": "", "posicao": posicao,
            "alternativas-TOTAL_FORMS": len(corretas), "alternativas-INITIAL_FORMS": 0,
            "alternativas-MIN_NUM_FORMS": 2, "alternativas-MAX_NUM_FORMS": 5,
        }
        for indice, correta in enumerate(corretas):
            dados[f"alternativas-{indice}-texto"] = f"Opção {indice}"
            if correta:
                dados[f"alternativas-{indice}-correta"] = "on"
        return dados

    def test_recusa_alternativas_sem_correta(self):
        resposta = self.client.post(
            reverse("admin:questionarios_questao_add"), self._dados(self.segunda, 2, [False, False])
        )

        self.assertContains(resposta, "Marque exatamente uma alternativa correta")

    def test_recusa_posicao_repetida(self):
        resposta = self.client.post(
            reverse("admin:questionarios_questao_add"), self._dados(self.segunda, 1, [True, False])
        )

        self.assertContains(resposta, "Posição já cadastrada para esta aula")

    def test_cria_questao_valida(self):
        resposta = self.client.post(
            reverse("admin:questionarios_questao_add"), self._dados(self.segunda, 2, [False, True, False])
        )

        self.assertRedirects(resposta, reverse("admin:questionarios_questao_changelist"))
        self.assertEqual(Questao.objects.filter(aula=self.segunda).count(), 2)

    def test_ultima_questao_de_aula_publicada_nao_tem_botao_excluir(self):
        unica = Questao.objects.get(aula=self.segunda)

        resposta = self.client.get(reverse("admin:questionarios_questao_delete", args=[unica.pk]))

        self.assertEqual(resposta.status_code, 403)

    def test_tentativas_sao_somente_leitura(self):
        QuestionarioService.corrigir(self.aula.pk, self.aluno, respostas(self.questoes, 3))
        tentativa = Tentativa.objects.get()

        self.assertEqual(self.client.get(reverse("admin:questionarios_tentativa_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:questionarios_tentativa_add")).status_code, 403)
        url = reverse("admin:questionarios_tentativa_delete", args=[tentativa.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
