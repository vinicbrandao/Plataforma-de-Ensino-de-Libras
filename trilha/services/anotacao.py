from django.utils import timezone

from ..exceptions import AcaoSomenteDoAluno
from ..models import AnotacaoAula
from .exibicao import ExibicaoAulaService


class AnotacaoService:
    """Anotação pessoal do aluno em cada aula (RF019). Só o próprio aluno a vê (RS004)."""

    @staticmethod
    def obter(aluno, aula) -> AnotacaoAula | None:
        return AnotacaoAula.objects.filter(aluno=aluno, aula=aula).first()

    @staticmethod
    def _aula_do_aluno(aluno, aula_id: int):
        # Aula despublicada dá AulaNaoEncontrada; a anotação fica gravada para quando ela voltar.
        aula = ExibicaoAulaService.verificar_acesso(aula_id, aluno)
        if aluno.is_staff:
            raise AcaoSomenteDoAluno
        return aula

    @classmethod
    def salvar(cls, aluno, aula_id: int, texto: str) -> AnotacaoAula:
        aula = cls._aula_do_aluno(aluno, aula_id)
        anotacao, _ = AnotacaoAula.objects.update_or_create(
            aluno=aluno, aula=aula, defaults={"texto": texto, "atualizada_em": timezone.now()}
        )
        return anotacao

    @classmethod
    def excluir(cls, aluno, aula_id: int) -> bool:
        aula = cls._aula_do_aluno(aluno, aula_id)
        apagadas, _ = AnotacaoAula.objects.filter(aluno=aluno, aula=aula).delete()
        return bool(apagadas)
