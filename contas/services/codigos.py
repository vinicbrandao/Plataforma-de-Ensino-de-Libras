import hashlib
import secrets


def gerar_codigo() -> str:
    """Código aleatório para links de uso único (RF004, RF005)."""
    return secrets.token_urlsafe(32)


def hash_do_codigo(codigo: str) -> str:
    """O banco guarda só o SHA-256; o código existe apenas no e-mail."""
    return hashlib.sha256((codigo or "").encode()).hexdigest()
