from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from questionarios.services import ConteudoInicialService


class Command(BaseCommand):
    help = (
        "Cadastra módulos, aulas, questões, categorias e sinais de demonstração (spec 0005). "
        "Pode rodar várias vezes sem duplicar. Os vídeos e legendas vêm de amostras/."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--pasta",
            type=Path,
            default=settings.BASE_DIR / "amostras",
            help="Pasta com os vídeos e legendas (padrão: amostras/ na raiz do projeto).",
        )

    def handle(self, *args, pasta: Path, **opcoes):
        self.stdout.write(f"Lendo arquivos de {pasta}")
        relatorio = ConteudoInicialService(pasta).criar()

        for tipo in ("categorias", "sinais", "módulos", "aulas", "questões"):
            self.stdout.write(
                f"  {tipo}: {relatorio.criados[tipo]} criados, {relatorio.existentes[tipo]} já existiam"
            )
        self.stdout.write(f"Aulas publicadas: {len(relatorio.publicadas)}")
        if relatorio.nao_publicadas:
            self.stdout.write(self.style.WARNING("Aulas não publicadas (falta vídeo ou legenda):"))
            for aula in relatorio.nao_publicadas:
                self.stdout.write(f"  - {aula}")
        if relatorio.faltando:
            self.stdout.write(self.style.WARNING(f"Arquivos faltando ou inválidos em {pasta}:"))
            for arquivo in relatorio.faltando:
                self.stdout.write(f"  - {arquivo}")
            self.stdout.write("Coloque os arquivos (veja amostras/LEIA-ME.md) e rode o comando de novo.")
        for erro in relatorio.erros:
            self.stdout.write(self.style.ERROR(f"Erro: {erro}"))
        if not (relatorio.faltando or relatorio.erros):
            self.stdout.write(self.style.SUCCESS("Conteúdo inicial completo."))
