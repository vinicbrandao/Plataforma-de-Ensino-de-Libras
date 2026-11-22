from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.utils import timezone

from contas.tests.fabricas import CPF_VALIDO_2, criar_admin, criar_aluno
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.models import Aula, ProgressoAula, ProgressoModulo
from trilha.services import ProgressoService

from .fabricas import criar_aula, criar_modulo


class TriggerDeConclusaoTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        cls.aula = criar_aula(criar_modulo(1), 1)

    def test_concluir_preenche_a_data_pela_trigger(self):
        progresso = ProgressoService.concluir(self.aluno, self.aula)

        self.assertEqual(progresso.status, ProgressoAula.Status.CONCLUIDA)
        self.assertIsNotNone(progresso.concluida_em)

    def test_concluir_de_novo_mantem_a_data_original(self):
        primeira = ProgressoService.concluir(self.aluno, self.aula).concluida_em

        segunda = ProgressoService.concluir(self.aluno, self.aula).concluida_em

        self.assertEqual(primeira, segunda)

    def test_trigger_impede_voltar_de_concluida(self):
        ProgressoService.concluir(self.aluno, self.aula)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProgressoAula.objects.filter(aluno=self.aluno).update(status="EM_ANDAMENTO")

    def test_trigger_mantem_a_data_mesmo_se_alguem_tentar_mudar(self):
        progresso = ProgressoService.concluir(self.aluno, self.aula)

        ProgressoAula.objects.filter(pk=progresso.pk).update(
            concluida_em=timezone.now() + timedelta(days=30)
        )

        progresso_relido = ProgressoAula.objects.get(pk=progresso.pk)
        self.assertEqual(progresso_relido.concluida_em, progresso.concluida_em)

    def test_registrar_acesso_cria_em_andamento_e_nao_altera_concluida(self):
        progresso = ProgressoService.registrar_acesso(self.aluno, self.aula)
        self.assertEqual(progresso.status, ProgressoAula.Status.EM_ANDAMENTO)

        ProgressoService.concluir(self.aluno, self.aula)
        progresso = ProgressoService.registrar_acesso(self.aluno, self.aula)

        self.assertEqual(progresso.status, ProgressoAula.Status.CONCLUIDA)

    def test_trigger_existe_no_banco(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tgname FROM pg_trigger WHERE tgname = 'trg_progresso_conclusao'"
            )
            self.assertIsNotNone(cursor.fetchone())


class ViewDeProgressoTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        cls.outro = criar_aluno(email="joao@exemplo.com", cpf=CPF_VALIDO_2, nome_completo="João")
        criar_admin()
        cls.modulo = criar_modulo(1)
        cls.aulas = [criar_aula(cls.modulo, posicao) for posicao in (1, 2, 3)]
        criar_aula(cls.modulo, 4, publicada=False)
        criar_modulo(2)  # Sem aulas publicadas: fica fora da view.

    def test_calcula_publicadas_concluidas_e_percentual_arredondado(self):
        ProgressoService.concluir(self.aluno, self.aulas[0])
        ProgressoService.registrar_acesso(self.aluno, self.aulas[1])

        linha = ProgressoModulo.objects.get(aluno=self.aluno, modulo=self.modulo)

        self.assertEqual((linha.aulas_publicadas, linha.aulas_concluidas, linha.percentual), (3, 1, 33))

    def test_tem_linha_por_aluno_e_ignora_administradores_e_modulos_vazios(self):
        self.assertEqual(ProgressoModulo.objects.count(), 2)
        self.assertEqual(ProgressoModulo.objects.get(aluno=self.outro).percentual, 0)

    def test_despublicar_recalcula_sem_apagar_a_conclusao(self):
        ProgressoService.concluir(self.aluno, self.aulas[0])
        Aula.objects.filter(pk=self.aulas[2].pk).update(publicada=False)

        linha = ProgressoModulo.objects.get(aluno=self.aluno, modulo=self.modulo)

        self.assertEqual((linha.aulas_publicadas, linha.percentual), (2, 50))
        self.assertTrue(ProgressoAula.objects.filter(status="CONCLUIDA").exists())
