from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from contas.tests.fabricas import criar_aluno
from contato.models import MensagemContato
from dicionario.tests.fabricas import MidiaTemporariaMixin
from trilha.models import Aula
from trilha.tests.fabricas import criar_aula, criar_modulo

TEXTO = "Não consigo ver a legenda da aula."


class MensagemContatoModeloTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno = criar_aluno()

    def criar(self, **campos) -> MensagemContato:
        valores = {"aluno": self.aluno, "assunto": "DUVIDA", "mensagem": TEXTO, **campos}
        return MensagemContato.objects.create(**valores)

    def test_nova_mensagem_comeca_aberta(self):
        self.assertEqual(self.criar().situacao, MensagemContato.Situacao.ABERTA)

    def test_banco_recusa_assunto_e_situacao_fora_das_opcoes(self):
        for campos in ({"assunto": "ELOGIO"}, {"situacao": "ARQUIVADA"}):
            with self.subTest(campos=campos), self.assertRaises(IntegrityError), transaction.atomic():
                self.criar(**campos)

    def test_banco_recusa_mensagem_com_menos_de_10_caracteres(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.criar(mensagem="Curta")

    def test_banco_recusa_resolvida_sem_resposta_ou_sem_data(self):
        casos = (
            {"situacao": "RESOLVIDA", "resposta": "", "resolvida_em": timezone.now()},
            {"situacao": "RESOLVIDA", "resposta": "Corrigido.", "resolvida_em": None},
            {"situacao": "ABERTA", "resposta": "", "resolvida_em": timezone.now()},
        )
        for campos in casos:
            with self.subTest(campos=campos), self.assertRaises(IntegrityError), transaction.atomic():
                self.criar(**campos)

    def test_banco_aceita_resolvida_com_resposta_e_data(self):
        mensagem = self.criar(situacao="RESOLVIDA", resposta="Corrigido.", resolvida_em=timezone.now())

        self.assertEqual(mensagem.situacao, "RESOLVIDA")

    def test_excluir_a_aula_mantem_a_mensagem_sem_a_aula(self):
        aula = criar_aula(criar_modulo(1), 1, publicada=False)
        mensagem = self.criar(assunto="ERRO_CONTEUDO", aula=aula)

        Aula.objects.filter(pk=aula.pk).delete()

        mensagem.refresh_from_db()
        self.assertIsNone(mensagem.aula)
