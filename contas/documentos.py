"""Value objects para documentos brasileiros usados no cadastro."""

import re
from dataclasses import dataclass


def _somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


@dataclass(frozen=True)
class Cpf:
    """CPF válido, guardado apenas com os 11 dígitos."""

    digitos: str

    @classmethod
    def de_texto(cls, texto: str) -> "Cpf":
        digitos = _somente_digitos(texto)
        if len(digitos) != 11 or digitos == digitos[0] * 11:
            raise ValueError("CPF inválido")
        if digitos[9:] != cls._calcular_verificadores(digitos[:9]):
            raise ValueError("CPF inválido")
        return cls(digitos)

    @staticmethod
    def _calcular_verificadores(base: str) -> str:
        numeros = [int(d) for d in base]
        for _ in range(2):
            peso_inicial = len(numeros) + 1
            soma = sum(n * peso for n, peso in zip(numeros, range(peso_inicial, 1, -1)))
            resto = soma % 11
            numeros.append(0 if resto < 2 else 11 - resto)
        return "".join(str(n) for n in numeros[-2:])

    @property
    def formatado(self) -> str:
        d = self.digitos
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"

    @property
    def parcial(self) -> str:
        d = self.digitos
        return f"***.{d[3:6]}.{d[6:9]}-**"

    def __str__(self) -> str:
        return self.formatado


@dataclass(frozen=True)
class Telefone:
    """Número de celular brasileiro com DDD."""

    digitos: str

    @classmethod
    def de_texto(cls, texto: str) -> "Telefone":
        digitos = _somente_digitos(texto)
        if len(digitos) != 11 or int(digitos[:2]) < 11 or digitos[2] != "9":
            raise ValueError("Telefone inválido")
        return cls(digitos)

    @property
    def formatado(self) -> str:
        d = self.digitos
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"

    def __str__(self) -> str:
        return self.formatado
