from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection, transaction
from django.test import SimpleTestCase, TestCase

from core.validadores import VideoMp4Validator
from dicionario.exceptions import CategoriaComSinaisAtivos, CategoriaJaCadastrada, TermoJaCadastrado
from dicionario.models import Categoria, Sinal
from dicionario.normalizacao import TextoNormalizado
from dicionario.services import CategoriaService, SinalService

from .fabricas import MidiaTemporariaMixin, criar_categoria, criar_sinal, video_mp4


class TextoNormalizadoTests(SimpleTestCase):
    def test_remove_acentos_maiusculas_e_espacos_extras(self):
        self.assertEqual(TextoNormalizado.de("  Mãe   (Família) ").valor, "mae (familia)")

    def test_texto_vazio_vira_vazio(self):
        self.assertEqual(TextoNormalizado.de("").valor, "")


class VideoMp4ValidatorTests(SimpleTestCase):
    def test_aceita_mp4_valido(self):
        VideoMp4Validator()(video_mp4())

    def test_recusa_arquivo_com_outra_assinatura_mesmo_com_extensao_mp4(self):
        falso = SimpleUploadedFile("sinal.mp4", b"%PDF-1.7 conteudo qualquer")

        with self.assertRaisesMessage(ValidationError, "envie um vídeo MP4 de até 50 MB"):
            VideoMp4Validator()(falso)

    def test_recusa_arquivo_acima_do_limite(self):
        with self.assertRaises(ValidationError):
            VideoMp4Validator(tamanho_maximo=10)(video_mp4())


class CategoriaServiceTests(MidiaTemporariaMixin, TestCase):
    def test_recusa_nome_repetido_com_acento_ou_maiuscula_diferente(self):
        criar_categoria("Família")

        with self.assertRaises(CategoriaJaCadastrada):
            criar_categoria("FAMILIA")

    def test_recusa_inativar_categoria_com_sinal_ativo(self):
        categoria = criar_categoria()
        criar_sinal(categoria=categoria)
        categoria.ativa = False

        with self.assertRaises(CategoriaComSinaisAtivos):
            CategoriaService.salvar(categoria)

    def test_aceita_inativar_categoria_so_com_sinais_inativos(self):
        categoria = criar_categoria()
        criar_sinal(categoria=categoria, ativo=False)
        categoria.ativa = False

        CategoriaService.salvar(categoria)

        self.assertFalse(Categoria.objects.get().ativa)

    def test_opcoes_ativas_nao_lista_categorias_inativas(self):
        ativa = criar_categoria("Cores")
        criar_categoria("Antiga", ativa=False)

        self.assertEqual(CategoriaService.opcoes_ativas(), [(ativa.id, "Cores")])


class SinalServiceTests(MidiaTemporariaMixin, TestCase):
    def test_preenche_termo_normalizado_e_gera_nome_do_arquivo(self):
        sinal = criar_sinal("Obrigado (agradecer)")

        self.assertEqual(sinal.termo_normalizado, "obrigado (agradecer)")
        self.assertRegex(sinal.video.name, r"^sinais/[0-9a-f]{32}\.mp4$")

    def test_recusa_termo_repetido_sem_acento(self):
        criar_sinal("Mãe")

        with self.assertRaises(TermoJaCadastrado):
            criar_sinal("mae")

    def test_editar_sem_mudar_o_termo_nao_acusa_duplicidade(self):
        sinal = criar_sinal("Mãe")
        sinal.descricao_execucao = "Mão na bochecha."

        SinalService.salvar(sinal)

        self.assertEqual(Sinal.objects.get().descricao_execucao, "Mão na bochecha.")

    def test_banco_recusa_classe_gramatical_fora_das_opcoes(self):
        sinal = criar_sinal("Mãe")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Sinal.objects.filter(pk=sinal.pk).update(classe_gramatical="PRONOME")

    def test_classe_gramatical_pode_ficar_vazia(self):
        sinal = criar_sinal("Mãe")

        self.assertEqual(sinal.classe_gramatical, "")


class IndiceTests(TestCase):
    def test_migracao_cria_indice_gin_trigram_no_termo_normalizado(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexdef FROM pg_indexes WHERE indexname = 'sinal_termo_trgm'"
            )
            (definicao,) = cursor.fetchone()

        self.assertIn("USING gin", definicao)
        self.assertIn("termo_normalizado gin_trgm_ops", definicao)
