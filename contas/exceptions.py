"""Exceções de domínio do app contas."""


class ErroDeContas(Exception):
    """Base das falhas previstas do app contas."""


class EmailJaCadastrado(ErroDeContas):
    pass


class CpfJaCadastrado(ErroDeContas):
    pass


class CadastroDeMenorIndisponivel(ErroDeContas):
    """Menores de 18 anos só se cadastram quando o RF002 existir."""


class CredenciaisInvalidas(ErroDeContas):
    pass


class LoginBloqueado(ErroDeContas):
    pass


class UsuarioDesativado(ErroDeContas):
    pass


class UsuarioNaoEncontrado(ErroDeContas):
    pass
