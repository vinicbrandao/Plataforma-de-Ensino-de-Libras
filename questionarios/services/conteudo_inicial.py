from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max

from dicionario.exceptions import ErroDeDicionario
from dicionario.models import Categoria, Sinal
from dicionario.normalizacao import TextoNormalizado
from dicionario.services import CategoriaService, SinalService
from trilha.exceptions import ErroDeTrilha
from trilha.models import Aula, Modulo
from trilha.services import AulaService, ModuloService

from .. import conteudo_inicial as dados
from ..exceptions import ErroDeQuestionario
from ..models import Alternativa, Questao
from .questao import QuestaoService

ERROS_PREVISTOS = (ErroDeDicionario, ErroDeTrilha, ErroDeQuestionario)


@dataclass
class RelatorioConteudo:
    """O que o comando criou, o que já existia e o que faltou (spec 0005)."""

    criados: Counter = field(default_factory=Counter)
    existentes: Counter = field(default_factory=Counter)
    publicadas: list[str] = field(default_factory=list)
    nao_publicadas: list[str] = field(default_factory=list)
    faltando: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)


class ConteudoInicialService:
    """Cadastra o conteúdo de demonstração pelos services, sem duplicar ao rodar de novo."""

    def __init__(self, pasta: Path):
        self.pasta = Path(pasta)
        self.relatorio = RelatorioConteudo()

    @staticmethod
    def nome_do_arquivo_do_sinal(termo: str) -> str:
        return TextoNormalizado.de(termo).valor.replace(" ", "-") + ".mp4"

    def criar(self) -> RelatorioConteudo:
        for nome, (classe, termos) in dados.CATEGORIAS.items():
            categoria = self._categoria(nome)
            for termo in termos:
                self._sinal(termo, classe, categoria)
        for numero_modulo, dados_modulo in enumerate(dados.MODULOS, start=1):
            modulo = self._modulo(numero_modulo, dados_modulo)
            if modulo is None:
                continue
            for numero_aula, dados_aula in enumerate(dados_modulo["aulas"], start=1):
                self._aula(modulo, numero_modulo, numero_aula, dados_aula)
        return self.relatorio

    # Arquivos

    def _arquivo(self, relativo: str, campo) -> ContentFile | None:
        """Lê o arquivo de amostras/ e o valida como o campo do model faria."""
        caminho = self.pasta / relativo
        if not caminho.is_file():
            self.relatorio.faltando.append(f"{relativo} (não encontrado)")
            return None
        conteudo = ContentFile(caminho.read_bytes(), name=caminho.name)
        try:
            for validador in campo.validators:
                validador(conteudo)
        except ValidationError as exc:
            self.relatorio.faltando.append(f"{relativo} (inválido: {exc.messages[0]})")
            return None
        return conteudo

    # Dicionário

    def _categoria(self, nome: str) -> Categoria | None:
        existente = Categoria.objects.filter(nome_normalizado=TextoNormalizado.de(nome).valor).first()
        if existente:
            self.relatorio.existentes["categorias"] += 1
            return existente
        try:
            categoria = CategoriaService.salvar(Categoria(nome=nome))
        except ERROS_PREVISTOS as exc:
            self.relatorio.erros.append(f"Categoria {nome}: {exc.mensagem}")
            return None
        self.relatorio.criados["categorias"] += 1
        return categoria

    def _sinal(self, termo: str, classe: str, categoria: Categoria | None) -> None:
        if Sinal.objects.filter(termo_normalizado=TextoNormalizado.de(termo).valor).exists():
            self.relatorio.existentes["sinais"] += 1
            return
        relativo = f"sinais/{self.nome_do_arquivo_do_sinal(termo)}"
        video = self._arquivo(relativo, Sinal._meta.get_field("video"))
        if video is None:
            return  # O vídeo é obrigatório: o sinal só é criado quando o arquivo existir.
        try:
            SinalService.salvar(
                Sinal(termo=termo, classe_gramatical=classe, categoria=categoria, video=video)
            )
        except ERROS_PREVISTOS as exc:
            self.relatorio.erros.append(f"Sinal {termo}: {exc.mensagem}")
            return
        self.relatorio.criados["sinais"] += 1

    # Trilha

    @staticmethod
    def _posicao_livre(desejada: int, ocupadas) -> int:
        if not ocupadas.filter(posicao=desejada).exists():
            return desejada
        return (ocupadas.aggregate(maior=Max("posicao"))["maior"] or 0) + 1

    def _modulo(self, numero: int, dados_modulo: dict) -> Modulo | None:
        existente = Modulo.objects.filter(titulo__iexact=dados_modulo["titulo"]).first()
        if existente:
            self.relatorio.existentes["módulos"] += 1
            return existente
        posicao = self._posicao_livre(numero, Modulo.objects.all())
        try:
            modulo = ModuloService.salvar(
                Modulo(titulo=dados_modulo["titulo"], descricao=dados_modulo["descricao"], posicao=posicao)
            )
        except ERROS_PREVISTOS as exc:
            self.relatorio.erros.append(f"Módulo {dados_modulo['titulo']}: {exc.mensagem}")
            return None
        self.relatorio.criados["módulos"] += 1
        return modulo

    def _aula(self, modulo: Modulo, numero_modulo: int, numero_aula: int, dados_aula: dict) -> None:
        rotulo = f"m{numero_modulo}-a{numero_aula} {dados_aula['titulo']}"
        existia = Aula.objects.filter(modulo=modulo, titulo__iexact=dados_aula["titulo"]).exists()
        try:
            with transaction.atomic():
                aula = self._aula_com_arquivos(modulo, numero_modulo, numero_aula, dados_aula)
                questoes_criadas = self._questoes(aula, dados_aula["questoes"])
                self._publicar_se_completa(aula)
        except ERROS_PREVISTOS as exc:
            self.relatorio.erros.append(f"Aula {rotulo}: {exc.mensagem}")
            return
        (self.relatorio.existentes if existia else self.relatorio.criados)["aulas"] += 1
        self.relatorio.criados["questões"] += questoes_criadas
        lista = self.relatorio.publicadas if aula.publicada else self.relatorio.nao_publicadas
        lista.append(rotulo)

    def _aula_com_arquivos(self, modulo: Modulo, numero_modulo: int, numero_aula: int, dados_aula: dict) -> Aula:
        aula = Aula.objects.filter(modulo=modulo, titulo__iexact=dados_aula["titulo"]).first()
        if aula is None:
            aula = Aula(
                modulo=modulo,
                titulo=dados_aula["titulo"],
                descricao=dados_aula["descricao"],
                posicao=self._posicao_livre(numero_aula, Aula.objects.filter(modulo=modulo)),
            )
        base = f"aulas/m{numero_modulo}-a{numero_aula}"
        if not aula.video:
            aula.video = self._arquivo(f"{base}.mp4", Aula._meta.get_field("video")) or ""
        if not aula.legenda:
            aula.legenda = self._arquivo(f"{base}.vtt", Aula._meta.get_field("legenda")) or ""
        return AulaService.salvar(aula)

    def _questoes(self, aula: Aula, questoes: list) -> int:
        """Cria as questões da aula, se ela ainda não tiver nenhuma. Devolve quantas criou."""
        if Questao.objects.filter(aula=aula).exists():
            self.relatorio.existentes["questões"] += len(questoes)
            return 0
        for posicao, (enunciado, alternativas) in enumerate(questoes, start=1):
            QuestaoService.validar_alternativas([correta for _, correta in alternativas])
            questao = QuestaoService.salvar(Questao(aula=aula, enunciado=enunciado, posicao=posicao))
            Alternativa.objects.bulk_create(
                Alternativa(questao=questao, texto=texto, correta=correta) for texto, correta in alternativas
            )
        return len(questoes)

    @staticmethod
    def _publicar_se_completa(aula: Aula) -> None:
        if aula.publicada or not (aula.video and aula.legenda):
            return
        aula.publicada = True
        AulaService.salvar(aula)
