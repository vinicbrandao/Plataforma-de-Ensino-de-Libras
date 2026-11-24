import importlib
import inspect
import pkgutil

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver, get_resolver
from django.views import View

APPS_DO_PROJETO = [app for app in settings.INSTALLED_APPS if not app.startswith("django.")]


def _modulos_de_views():
    for app in APPS_DO_PROJETO:
        pacote = importlib.import_module(f"{app}.views")
        yield pacote
        for info in pkgutil.iter_modules(pacote.__path__):
            yield importlib.import_module(f"{pacote.__name__}.{info.name}")


def _padroes_de_url(padroes):
    for padrao in padroes:
        if isinstance(padrao, URLPattern):
            yield padrao
        elif isinstance(padrao, URLResolver) and padrao.app_name != "admin":
            yield from _padroes_de_url(padrao.url_patterns)


class ArquiteturaTests(SimpleTestCase):
    def test_classes_de_view_herdam_diretamente_de_view(self):
        classes = [
            classe
            for modulo in _modulos_de_views()
            for nome, classe in inspect.getmembers(modulo, inspect.isclass)
            if classe.__module__ == modulo.__name__ and nome.endswith("View")
        ]

        self.assertTrue(classes, "Nenhuma classe de view foi encontrada.")
        for classe in classes:
            with self.subTest(view=classe.__name__):
                self.assertIn(View, classe.__bases__)

    def test_rotas_apontam_para_views_criadas_com_as_view(self):
        padroes = [
            padrao
            for padrao in _padroes_de_url(get_resolver().url_patterns)
            if not str(padrao.pattern).startswith("^media/")
        ]

        self.assertTrue(padroes, "Nenhuma rota foi encontrada.")
        for padrao in padroes:
            with self.subTest(rota=padrao.name):
                self.assertTrue(hasattr(padrao.callback, "view_class"))


class AbstracaoTests(SimpleTestCase):
    """As classes base abstratas não podem ser instanciadas sem implementar o método abstrato (POO)."""

    def test_validador_de_arquivo_base_e_abstrato(self):
        from core.validadores import ArquivoValidator, VideoMp4Validator

        with self.assertRaises(TypeError):
            ArquivoValidator()
        self.assertTrue(VideoMp4Validator().conteudo_valido(b"\x00\x00\x00\x18ftypisom"))

    def test_acao_na_aula_exige_executar(self):
        from trilha.views.participacao import ParticipacaoNaAulaMixin

        with self.assertRaises(TypeError):
            ParticipacaoNaAulaMixin()
