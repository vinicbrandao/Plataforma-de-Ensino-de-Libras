# Spec 0011: Recuperação de senha

- **Status:** Implementado
- **Requisitos:** RF-92 a RF-96 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF004 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0005](../adr/0005-emails-no-console-em-desenvolvimento.md)
- **Depende de:** [Spec 0001](0001-fundacao-e-contas.md)

Quem esqueceu a senha recebe por e-mail um link de uso único para definir outra. Em desenvolvimento, o e-mail aparece no terminal (ADR 0005).

O `PasswordResetTokenGenerator` do Django não é usado: o token dele não é invalidado por uma nova solicitação, como exige o RS008. O código fica em tabela própria.

## Models (`contas/models/`)

### `TokenRedefinicaoSenha`

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `ForeignKey(Usuario, PROTECT, related_name="tokens_redefinicao")` | |
| `codigo_hash` | `CharField(64, unique=True)` | SHA-256 do código. O código em si só existe no e-mail |
| `criado_em` | `DateTimeField(default=timezone.now)` | |
| `expira_em` | `DateTimeField` | `criado_em` + 30 minutos (RF-93) |
| `usado_em` | `DateTimeField(null=True, blank=True)` | Registro da redefinição (RF-96) |
| `invalidado_em` | `DateTimeField(null=True, blank=True)` | Preenchido por uma nova solicitação |

Constraint `token_expira_depois_de_criado`: `expira_em > criado_em`.

### `SolicitacaoRedefinicao`

Registra toda solicitação, exista o e-mail ou não, para o limite por hora e o registro do RF-96.

| Campo | Tipo | Regras |
|---|---|---|
| `chave` | `CharField(64)` | HMAC do e-mail normalizado, como em `FalhaLogin`, para não guardar e-mails digitados que não existem |
| `criada_em` | `DateTimeField(default=timezone.now)` | Índice com `chave` |

## Exceções (`contas/exceptions.py`)

| Exceção | Mensagem |
|---|---|
| `MuitasSolicitacoes` | "Muitas solicitações. Tente novamente mais tarde" |
| `LinkInvalido` | "Link expirado ou inválido" |
| `SenhaIgualAAtual` | "A nova senha deve ser diferente da senha atual" |

## `RedefinicaoSenhaService` (`contas/services/redefinicao.py`)

| Método | Regra |
|---|---|
| `solicitar(email, montar_link: Callable[[str], str]) -> None` | Normaliza o e-mail. Com 3 ou mais solicitações da mesma chave na última hora, levanta `MuitasSolicitacoes` (RF-94). Registra a solicitação. Se o e-mail é de um usuário ativo, invalida os tokens abertos dele, cria um token com `secrets.token_urlsafe(32)` e envia o e-mail com o link montado pela view. Caso contrário, não faz mais nada, e a view mostra a mesma mensagem (RS002) |
| `validar(codigo, para_atualizar=False) -> TokenRedefinicaoSenha` | Com `para_atualizar`, trava a linha do token (`select_for_update`). Token existente, não usado, não invalidado, não expirado e de usuário ativo. Caso contrário, `LinkInvalido` (RF-93) |
| `redefinir(codigo, nova_senha) -> None` | Em `transaction.atomic()` com `select_for_update` no token: valida, recusa a senha atual (`SenhaIgualAAtual`), grava com `set_password`, marca `usado_em` e invalida os outros tokens do usuário. Trocar a senha muda o hash de sessão, então o Django encerra todas as sessões do usuário (RF-95). Depois do commit, envia o e-mail avisando da alteração |

O `montar_link` é uma função recebida da view, que conhece o domínio da requisição. Assim, o service não recebe `request`.

## Forms (`contas/forms/redefinicao.py`)

- `SolicitarRedefinicaoForm`: `email` (`EmailField`, até 200 caracteres).
- `NovaSenhaForm`: `nova_senha` e `confirmacao`, com as mesmas regras de senha do cadastro (`validate_password` e a mensagem única do RF001). A validação de senha do `CadastroForm` passou para o `ValidacaoDeSenhaMixin` (`contas/forms/senha.py`), usado pelos dois forms.

## Rotas (`app_name = "contas"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/senha/esqueci/` | `contas:esqueci_senha` | `EsqueciSenhaView` | GET, POST | Qualquer pessoa |
| `/senha/redefinir/<str:codigo>/` | `contas:redefinir_senha_link` | `RedefinirSenhaView` | GET | Qualquer pessoa |
| `/senha/redefinir/` | `contas:redefinir_senha` | `RedefinirSenhaView` | GET, POST | Quem abriu um link válido |

## Comportamento

- **`EsqueciSenhaView.post`:** chama `solicitar`, mostra "Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha" e leva ao login. `MuitasSolicitacoes` reapresenta o formulário com a mensagem própria.
- **Link do e-mail:** o GET com o código valida o token, guarda o código na sessão e redireciona para a rota sem o código. O código sai do endereço e não vaza pelo histórico do navegador nem pelo cabeçalho Referer, como faz o Django.
- **`RedefinirSenhaView`:**
  - GET mostra o formulário se a sessão tem um código válido. Caso contrário, mostra "Link expirado ou inválido", com status 400 e o link para pedir outro.
  - POST chama `redefinir`, mostra "Senha alterada com sucesso" e leva ao login.
- A tela de login ganha o link "Esqueci minha senha" (RF-92).

## Limites aceitos nesta versão

- A chave do limite é o e-mail, como pede o RF004. Não há limite por IP.

## Testes

- [x] A mensagem é a mesma para e-mail cadastrado, não cadastrado e de usuário desativado, e só o usuário ativo recebe e-mail.
- [x] A quarta solicitação na mesma hora é recusada, e depois de uma hora volta a ser aceita.
- [x] O link vale por 30 minutos, uma única vez, e uma nova solicitação invalida o anterior.
- [x] A nova senha segue as regras do RF001, precisa bater com a confirmação e ser diferente da atual.
- [x] Depois da redefinição, as outras sessões do usuário deixam de valer, e o e-mail de aviso é enviado.
- [x] O código não fica no endereço depois do primeiro acesso.
- [x] O banco não guarda o código, só o hash.
