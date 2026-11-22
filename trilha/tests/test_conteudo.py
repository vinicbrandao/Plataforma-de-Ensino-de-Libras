from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import SimpleTestCase, TestCase

from contas.tests.fabricas import criar_aluno
from core.validadores import LegendaVttValidator, MaterialValidator, VideoMp4Validator
from dicionario.tests.fabricas import BYTES_MP4, MidiaTemporariaMixin
from trilha.exceptions import AulaIncompletaParaPublicar, PosicaoJaCadastrada, TituloJaCadastrado
from trilha.models import Aula, MaterialComplementar, Modulo
from trilha.services import AulaService, ModuloService, ProgressoService

from .fabricas import BYTES_PDF, BYTES_PNG, BYTES_VTT, criar_aula, criar_modulo


def arquivo(conteudo: bytes, nome: str = "arquivo") -> SimpleUploadedFile:
    return SimpleUploadedFile(nome, conteudo)


class ValidadoresTests(SimpleTestCase):
    def test_aceitam_os_formatos_corretos(self):
        VideoMp4Validator()(arquivo(BYTES_MP4))
        LegendaVttValidator()(arquivo(BYTES_VTT))
        LegendaVttValidator()(arquivo(b"\xef\xbb\xbf" + BYTES_VTT))
        MaterialValidator()(arquivo(BYTES_PDF))
        MaterialValidator()(arquivo(BYTES_PNG))

    def test_recusam_assinatura_falsa(self):
        casos = [
            (LegendaVttValidator(), b"1\n00:00:00,000 --> 00:00:02,000\nSRT"),
            (MaterialValidator(), b"MZ executavel"),
            (VideoMp4Validator(), BYTES_PDF),
        ]
        for validador, conteudo in casos:
            with self.subTest(validador=type(validador).__name__), self.assertRaises(ValidationError):
                validador(arquivo(conteudo, "falso.vtt"))

    def test_recusam_arquivo_acima_do_limite(self):
        with self.assertRaisesMessage(ValidationError, "envie um PDF, JPG ou PNG de até"):
            MaterialValidator(tamanho_maximo=10)(arquivo(BYTES_PDF))

    def test_extensao_do_material_vem_da_assinatura(self):
        self.assertEqual(MaterialValidator.extensao(BYTES_PNG), "png")
        self.assertIsNone(MaterialValidator.extensao(b"texto"))


class ModuloServiceTests(TestCase):
    def test_recusa_titulo_repetido_sem_diferenciar_maiusculas_e_espacos(self):
        criar_modulo(1, "Primeiros sinais")

        with self.assertRaises(TituloJaCadastrado):
            criar_modulo(2, "  PRIMEIROS   sinais ")

    def test_recusa_posicao_repetida(self):
        criar_modulo(1)

        with self.assertRaises(PosicaoJaCadastrada):
            criar_modulo(1, "Outro título")

    def test_remove_espacos_repetidos_do_titulo(self):
        self.assertEqual(criar_modulo(1, "  Saudações   e  cumprimentos ").titulo, "Saudações e cumprimentos")

    def test_banco_recusa_posicao_zero(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Modulo.objects.create(titulo="X", descricao="Y", posicao=0)


class AulaServiceTests(MidiaTemporariaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.modulo = criar_modulo(1)
        cls.outro_modulo = criar_modulo(2)

    def test_titulo_e_posicao_sao_unicos_dentro_do_modulo(self):
        criar_aula(self.modulo, 1, titulo="Alfabeto")

        with self.assertRaises(TituloJaCadastrado):
            criar_aula(self.modulo, 2, titulo="alfabeto")
        with self.assertRaises(PosicaoJaCadastrada):
            criar_aula(self.modulo, 1, titulo="Números")
        criar_aula(self.outro_modulo, 1, titulo="Alfabeto")  # Outro módulo: permitido.

    def test_nao_publica_sem_video_ou_legenda(self):
        aula = Aula(modulo=self.modulo, titulo="Sem vídeo", descricao="D", posicao=1, publicada=True)

        with self.assertRaises(AulaIncompletaParaPublicar):
            AulaService.salvar(aula)

    def test_banco_recusa_aula_publicada_incompleta(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Aula.objects.create(modulo=self.modulo, titulo="X", descricao="Y", posicao=3, publicada=True)

    def test_salva_aula_nao_publicada_sem_arquivos(self):
        aula = criar_aula(self.modulo, 1, publicada=False)

        self.assertFalse(aula.publicada)
        self.assertEqual(aula.video.name, "")

    def test_arquivos_recebem_nomes_gerados(self):
        aula = criar_aula(self.modulo, 1)
        material = MaterialComplementar.objects.create(
            aula=aula, titulo="Tabela", arquivo=arquivo(BYTES_PNG, "tabela.pdf")
        )

        self.assertRegex(aula.video.name, r"^aulas/videos/[0-9a-f]{32}\.mp4$")
        self.assertRegex(aula.legenda.name, r"^aulas/legendas/[0-9a-f]{32}\.vtt$")
        self.assertRegex(material.arquivo.name, r"^aulas/materiais/[0-9a-f]{32}\.png$")


class ExclusaoProtegidaTests(MidiaTemporariaMixin, TestCase):
    def test_modulo_com_aulas_nao_e_excluido(self):
        modulo = criar_modulo(1)
        criar_aula(modulo, 1, publicada=False)

        with self.assertRaises(ProtectedError):
            modulo.delete()

    def test_aula_com_progresso_nao_e_excluida(self):
        aula = criar_aula(criar_modulo(1), 1)
        ProgressoService.registrar_acesso(criar_aluno(), aula)

        with self.assertRaises(ProtectedError):
            aula.delete()
