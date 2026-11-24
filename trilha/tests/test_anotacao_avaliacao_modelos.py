from django.db import IntegrityError, transaction
from django.test import TestCase

from contas.tests.fabricas import criar_aluno
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.models import AnotacaoAula, AvaliacaoAula

from .fabricas import criar_aula, criar_modulo


class AnotacaoEAvaliacaoModeloTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()
        cls.aula = criar_aula(criar_modulo(1), 1)

    def test_banco_recusa_duas_anotacoes_do_aluno_na_mesma_aula(self):
        AnotacaoAula.objects.create(aluno=self.aluno, aula=self.aula, texto="Primeira")

        with self.assertRaises(IntegrityError), transaction.atomic():
            AnotacaoAula.objects.create(aluno=self.aluno, aula=self.aula, texto="Segunda")

    def test_banco_recusa_anotacao_vazia(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AnotacaoAula.objects.create(aluno=self.aluno, aula=self.aula, texto="")

    def test_banco_recusa_nota_fora_de_1_a_5(self):
        for nota in (0, 6):
            with self.subTest(nota=nota), self.assertRaises(IntegrityError), transaction.atomic():
                AvaliacaoAula.objects.create(aluno=self.aluno, aula=self.aula, nota=nota)

    def test_banco_aceita_notas_de_1_a_5(self):
        AvaliacaoAula.objects.create(aluno=self.aluno, aula=self.aula, nota=1)
        AvaliacaoAula.objects.filter(aluno=self.aluno).update(nota=5)

        self.assertEqual(AvaliacaoAula.objects.get().nota, 5)

    def test_banco_recusa_duas_avaliacoes_do_aluno_na_mesma_aula(self):
        AvaliacaoAula.objects.create(aluno=self.aluno, aula=self.aula, nota=4)

        with self.assertRaises(IntegrityError), transaction.atomic():
            AvaliacaoAula.objects.create(aluno=self.aluno, aula=self.aula, nota=5)
