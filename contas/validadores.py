"""Validadores de senha do projeto."""

from django.core.exceptions import ValidationError

MENSAGEM_SENHA = "A senha deve ter ao menos 8 caracteres, com letras e números"


class LetrasENumerosValidator:
    """Exige ao menos uma letra e um dígito na senha (RF001)."""

    def validate(self, password: str, user=None) -> None:
        tem_letra = any(c.isalpha() for c in password)
        tem_digito = any(c.isdigit() for c in password)
        if not (tem_letra and tem_digito):
            raise ValidationError(MENSAGEM_SENHA, code="senha_sem_letras_e_numeros")

    def get_help_text(self) -> str:
        return MENSAGEM_SENHA
