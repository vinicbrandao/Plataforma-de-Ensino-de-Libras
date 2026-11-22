from django.test import SimpleTestCase

from contas.documentos import Cpf, Telefone


class CpfTests(SimpleTestCase):
    def test_aceita_cpf_valido_com_e_sem_pontuacao(self):
        self.assertEqual(Cpf.de_texto("529.982.247-25").formatado, "529.982.247-25")
        self.assertEqual(Cpf.de_texto("52998224725").formatado, "529.982.247-25")

    def test_rejeita_digito_verificador_errado(self):
        with self.assertRaises(ValueError):
            Cpf.de_texto("529.982.247-26")

    def test_rejeita_sequencia_repetida(self):
        with self.assertRaises(ValueError):
            Cpf.de_texto("111.111.111-11")

    def test_rejeita_tamanho_errado(self):
        for texto in ("5299822472", "529982247250", ""):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                Cpf.de_texto(texto)

    def test_parcial_esconde_inicio_e_verificadores(self):
        self.assertEqual(Cpf.de_texto("52998224725").parcial, "***.982.247-**")


class TelefoneTests(SimpleTestCase):
    def test_formata_celular_com_ou_sem_mascara(self):
        self.assertEqual(Telefone.de_texto("11912345678").formatado, "(11) 91234-5678")
        self.assertEqual(Telefone.de_texto("(11) 91234-5678").formatado, "(11) 91234-5678")

    def test_rejeita_numero_que_nao_e_celular(self):
        for texto in ("1132345678", "11812345678", "05912345678"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                Telefone.de_texto(texto)
