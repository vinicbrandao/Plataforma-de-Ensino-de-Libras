import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class TextoNormalizado:
    """Forma de um texto sem acentos, maiúsculas nem espaços extras (RF010, RF015)."""

    valor: str

    @classmethod
    def de(cls, texto: str) -> "TextoNormalizado":
        decomposto = unicodedata.normalize("NFKD", texto or "")
        sem_acentos = "".join(c for c in decomposto if not unicodedata.combining(c))
        return cls(re.sub(r"\s+", " ", sem_acentos.casefold()).strip())

    def __str__(self) -> str:
        return self.valor
