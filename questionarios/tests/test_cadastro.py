from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from contas.tests.fabricas import criar_admin
from dicionario.exceptions import SinalEmUso
from dicionario.services import SinalService
from dicionario.tests.fabricas import MidiaTemporariaMixin, criar_sinal
from questionarios.exceptions import (
    AlternativaCorretaInvalida,
    PosicaoDeQuestaoJaCadastrada,
    QuantidadeDeAlternativasInvalida,
    UltimaQuestaoDeAulaPublicada,
)
from questionarios.models import Alternativa, Questao
from questionarios.services import QuestaoService
from trilha.exceptions import AulaIncompletaParaPublicar
from trilha.models import Aula
from trilha.services import AulaService
from trilha.tests.fabricas import criar_aula, criar_modulo, legenda, video

from .fabricas import criar_questao


class ValidarAlternativasTests(SimpleTestCase):
    def test_exige_de_2_a_5_alternativas(self):
        for corretas in ([True], [True, False, False, False, False, False]):
            with self.subTest(quantidade=len(corretas)), self.assertRaises(QuantidadeDeAlternativasInvalida):
                QuestaoService.validar_alternativas(corretas)

    def test_exige_exatamente_uma_correta(self):
        for corretas in ([False, False], [True, True, False]):
            with self.subTest(corretas=corretas), self.assertRaises(AlternativaCorretaInvalida):
                QuestaoService.validar_alternativas(corretas)

    def test_aceita_conjunto_valido(self):
        QuestaoService.validar_alternativas([False, True, False, False, False])


class QuestaoServiceTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        modulo = criar_modulo(1)
        cls.aula = criar_aula(modulo, 1)
        cls.outra_aula = criar_aula(modulo, 2)

    def test_banco_recusa_duas_alternativas_corretas(self):
        questao = criar_questao(self.aula)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Alternativa.objects.create(questao=questao, texto="Outra correta", correta=True)

    def test_posicao_unica_na_aula(self):
        criar_questao(self.aula, 1)

        with self.assertRaises(PosicaoDeQuestaoJaCadastrada):
            QuestaoService.salvar(Questao(aula=self.aula, enunciado="X", posicao=1))
        QuestaoService.salvar(Questao(aula=self.outra_aula, enunciado="X", posicao=1))

    def test_ultima_questao_de_aula_publicada_nao_e_excluida(self):
        questao = criar_questao(self.aula)

        with self.assertRaises(UltimaQuestaoDeAulaPublicada):
            QuestaoService.excluir(questao)

    def test_com_outra_questao_a_exclusao_funciona(self):
        primeira = criar_questao(self.aula, 1)
        criar_questao(self.aula, 2)

        QuestaoService.excluir(primeira)

        self.assertEqual(Questao.objects.filter(aula=self.aula).count(), 1)


class PublicacaoExigeQuestaoTests(MidiaTemporariaMixin, TestCase):
    def setUp(self):
        self.aula = criar_aula(criar_modulo(1), 1, publicada=False)
        self.aula.video = video()
        self.aula.legenda = legenda()
        AulaService.salvar(self.aula)
        self.aula.publicada = True

    def test_service_recusa_publicar_sem_questao(self):
        with self.assertRaises(AulaIncompletaParaPublicar):
            AulaService.salvar(self.aula)

    def test_service_publica_com_questao(self):
        criar_questao(self.aula)

        AulaService.salvar(self.aula)

        self.assertTrue(Aula.objects.get(pk=self.aula.pk).publicada)

    def test_admin_publica_aula_existente_com_questao(self):
        criar_questao(self.aula)
        self.client.force_login(criar_admin())
        dados = {
            "modulo": self.aula.modulo_id, "titulo": self.aula.titulo, "descricao": "D",
            "posicao": 1, "texto_apoio": "", "publicada": "on",
            "materiais-TOTAL_FORMS": 0, "materiais-INITIAL_FORMS": 0,
        }

        resposta = self.client.post(reverse("admin:trilha_aula_change", args=[self.aula.pk]), dados)

        self.assertRedirects(resposta, reverse("admin:trilha_aula_changelist"))
        self.assertTrue(Aula.objects.get(pk=self.aula.pk).publicada)


class SinalUsadoEmQuestaoTests(MidiaTemporariaMixin, TestCase):
    def test_sinal_usado_em_aula_publicada_nao_e_inativado(self):
        sinal = criar_sinal("Mãe")
        criar_questao(criar_aula(criar_modulo(1), 1), sinal=sinal)
        sinal.ativo = False

        with self.assertRaises(SinalEmUso):
            SinalService.salvar(sinal)

    def test_sinal_usado_so_em_aula_nao_publicada_pode_ser_inativado(self):
        sinal = criar_sinal("Mãe")
        criar_questao(criar_aula(criar_modulo(1), 1, publicada=False), sinal=sinal)
        sinal.ativo = False

        SinalService.salvar(sinal)

    def test_sinal_usado_em_questao_nao_e_excluido(self):
        sinal = criar_sinal("Mãe")
        criar_questao(criar_aula(criar_modulo(1), 1, publicada=False), sinal=sinal)

        with self.assertRaises(ProtectedError):
            sinal.delete()
