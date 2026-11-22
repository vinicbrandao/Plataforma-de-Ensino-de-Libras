import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from dicionario.models import Categoria, Sinal
from dicionario.tests.fabricas import BYTES_MP4, MidiaTemporariaMixin
from questionarios import conteudo_inicial as dados
from questionarios.models import Questao
from questionarios.services import ConteudoInicialService
from trilha.models import Aula, Modulo
from trilha.tests.fabricas import BYTES_VTT, criar_modulo

TOTAL_DE_ARQUIVOS = 27  # 6 vídeos e 6 legendas de aulas + 15 vídeos de sinais.


def preencher_amostras(pasta: Path) -> None:
    """Cria arquivos falsos, mas com assinatura válida, com os nomes esperados."""
    (pasta / "aulas").mkdir(parents=True, exist_ok=True)
    (pasta / "sinais").mkdir(parents=True, exist_ok=True)
    for numero_modulo, modulo in enumerate(dados.MODULOS, start=1):
        for numero_aula in range(1, len(modulo["aulas"]) + 1):
            base = pasta / "aulas" / f"m{numero_modulo}-a{numero_aula}"
            base.with_suffix(".mp4").write_bytes(BYTES_MP4)
            base.with_suffix(".vtt").write_bytes(BYTES_VTT)
    for _, termos in dados.CATEGORIAS.values():
        for termo in termos:
            nome = ConteudoInicialService.nome_do_arquivo_do_sinal(termo)
            (pasta / "sinais" / nome).write_bytes(BYTES_MP4)


class ConteudoInicialTests(MidiaTemporariaMixin, TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.pasta, ignore_errors=True)

    def _rodar(self) -> str:
        saida = StringIO()
        call_command("criar_conteudo_inicial", pasta=self.pasta, stdout=saida)
        return saida.getvalue()

    def test_com_todos_os_arquivos_cria_tudo_publicado(self):
        preencher_amostras(self.pasta)

        saida = self._rodar()

        self.assertEqual(Categoria.objects.count(), 3)
        self.assertEqual(Sinal.objects.count(), 15)
        self.assertEqual(Modulo.objects.count(), 3)
        self.assertEqual(Aula.objects.filter(publicada=True).count(), 6)
        self.assertEqual(Questao.objects.count(), 18)
        self.assertIn("Conteúdo inicial completo.", saida)

    def test_rodar_duas_vezes_nao_duplica(self):
        preencher_amostras(self.pasta)
        self._rodar()

        saida = self._rodar()

        contagens = (Categoria.objects.count(), Sinal.objects.count(), Modulo.objects.count(),
                     Aula.objects.count(), Questao.objects.count())
        self.assertEqual(contagens, (3, 15, 3, 6, 18))
        self.assertIn("aulas: 0 criados, 6 já existiam", saida)

    def test_sem_arquivos_cria_o_que_da_e_lista_o_que_falta(self):
        saida = self._rodar()

        self.assertEqual(Categoria.objects.count(), 3)
        self.assertEqual(Sinal.objects.count(), 0)
        self.assertEqual(Aula.objects.filter(publicada=False).count(), 6)
        self.assertEqual(Questao.objects.count(), 18)
        self.assertEqual(saida.count("(não encontrado)"), TOTAL_DE_ARQUIVOS)
        self.assertIn("aulas/m1-a1.mp4 (não encontrado)", saida)
        self.assertIn("sinais/bom-dia.mp4 (não encontrado)", saida)
        self.assertIn("Aulas não publicadas", saida)

    def test_acrescentar_arquivos_e_rodar_de_novo_publica_as_aulas(self):
        self._rodar()
        preencher_amostras(self.pasta)

        self._rodar()

        self.assertEqual(Aula.objects.filter(publicada=True).count(), 6)
        self.assertEqual(Sinal.objects.count(), 15)
        self.assertEqual(Questao.objects.count(), 18)

    def test_arquivo_com_assinatura_invalida_conta_como_faltando(self):
        preencher_amostras(self.pasta)
        (self.pasta / "aulas" / "m1-a1.vtt").write_bytes(b"1\n00:00:00,000 --> 00:00:02,000\nSRT\n")

        saida = self._rodar()

        self.assertIn("aulas/m1-a1.vtt (inválido:", saida)
        self.assertFalse(Aula.objects.get(titulo="O que é Libras").publicada)
        self.assertEqual(Aula.objects.filter(publicada=True).count(), 5)

    def test_modulo_da_equipe_na_posicao_1_nao_impede_a_criacao(self):
        criar_modulo(1, "Módulo da equipe")

        self._rodar()

        self.assertEqual(Modulo.objects.get(titulo="Primeiros passos").posicao, 2)
        self.assertEqual(Modulo.objects.count(), 4)
