"""Exceções de domínio do app contas."""


class ErroDeContas(Exception):
    """Base das falhas previstas do app contas."""


class EmailJaCadastrado(ErroDeContas):
    pass


class CpfJaCadastrado(ErroDeContas):
    pass


class ResponsavelObrigatorio(ErroDeContas):
    """Menor de 18 anos sem os dados do responsável legal (RF002)."""

    mensagem = "Campo obrigatório não preenchido"


class CpfDoResponsavelIgualAoDoAluno(ErroDeContas):
    mensagem = "O CPF do responsável deve ser diferente do CPF do aluno"


class ResponsavelSomenteLeitura(ErroDeContas):
    """Com 18 anos ou mais, os dados do responsável ficam só para leitura (RF002)."""


class CredenciaisInvalidas(ErroDeContas):
    pass


class LoginBloqueado(ErroDeContas):
    pass


class UsuarioDesativado(ErroDeContas):
    pass


class UsuarioNaoEncontrado(ErroDeContas):
    pass


class MuitasSolicitacoes(ErroDeContas):
    """Mais de 3 pedidos de redefinição por hora para o mesmo e-mail (RF004)."""

    mensagem = "Muitas solicitações. Tente novamente mais tarde"


class LinkInvalido(ErroDeContas):
    """Link de redefinição usado, vencido, substituído ou inexistente (RF004, RS008)."""

    mensagem = "Link expirado ou inválido"


class SenhaIgualAAtual(ErroDeContas):
    mensagem = "A nova senha deve ser diferente da senha atual"


class SenhaAtualIncorreta(ErroDeContas):
    mensagem = "Senha atual incorreta"


class LinkConfirmacaoInvalido(ErroDeContas):
    """Link de troca de e-mail usado, vencido, substituído ou inexistente (RF005, RS011)."""

    mensagem = "Link de confirmação expirado ou inválido"
