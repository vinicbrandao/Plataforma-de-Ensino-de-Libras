from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from ..validadores import MENSAGEM_SENHA

SENHAS_DIFERENTES = "As senhas informadas não coincidem"
# Erros de senha que o RF001 resume em uma única mensagem.
CODIGOS_DA_MENSAGEM_DE_SENHA = {
    "password_too_short",
    "password_entirely_numeric",
    "senha_sem_letras_e_numeros",
}


class ValidacaoDeSenhaMixin:
    """Regras de senha do RF001, usadas no cadastro e na redefinição (RF004)."""

    def validar_senha_nova(self, dados: dict, campo: str, campo_confirmacao: str, usuario) -> None:
        senha = dados.get(campo)
        if not senha:
            return
        if senha != dados.get(campo_confirmacao):
            self.add_error(campo_confirmacao, SENHAS_DIFERENTES)
        try:
            validate_password(senha, user=usuario)
        except ValidationError as exc:
            for mensagem in self.mensagens_de_senha(exc):
                self.add_error(campo, mensagem)

    @staticmethod
    def mensagens_de_senha(exc: ValidationError) -> list[str]:
        mensagens = []
        for erro in exc.error_list:
            mensagem = MENSAGEM_SENHA if erro.code in CODIGOS_DA_MENSAGEM_DE_SENHA else erro.messages[0]
            if mensagem not in mensagens:
                mensagens.append(mensagem)
        return mensagens
