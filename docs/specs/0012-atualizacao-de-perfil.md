# Spec 0012: Atualização de perfil

- **Status:** Implementado
- **Requisitos:** RF-97 a RF-104 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF005 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0005](../adr/0005-emails-no-console-em-desenvolvimento.md)
- **Depende de:** [Spec 0001](0001-fundacao-e-contas.md), [Spec 0011](0011-recuperacao-de-senha.md) (regras da nova senha e `SenhaIgualAAtual`)

O aluno consulta e altera os próprios dados, troca a senha e envia uma foto. Toda alteração fica no histórico.

## Mudanças em `Usuario`

| Campo | Tipo | Regras |
|---|---|---|
| `foto` | `FileField(upload_to=caminho_foto, blank=True)` | JPG ou PNG de até 2 MB, validado pelo tipo real por um novo `ImagemPerfilValidator` em `core/validadores.py`. O nome é um UUID, sem dados pessoais (RS004, RS012). Usa `FileField`, e não `ImageField`, para não depender do Pillow |
| `receber_lembretes` | `BooleanField(default=True)` | Preferência usada pelos lembretes (RF011), que não estão na versão 1 |

## Models (`contas/models/`)

### `HistoricoAlteracao`

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `ForeignKey(Usuario, PROTECT, related_name="historico")` | |
| `campo` | `CharField(60)` | Nome do campo, como `telefone` ou `senha` |
| `valor_anterior` | `CharField(255, blank=True)` | Vazio para a senha (RS003) |
| `valor_novo` | `CharField(255, blank=True)` | Vazio para a senha |
| `alterado_em` | `DateTimeField(default=timezone.now)` | |

Não tem Admin e nenhum service altera ou exclui as linhas (RS007).

### `ConfirmacaoEmail`

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `ForeignKey(Usuario, PROTECT, related_name="confirmacoes_email")` | |
| `novo_email` | `EmailField(200)` | |
| `codigo_hash` | `CharField(64, unique=True)` | SHA-256 do código |
| `criado_em` | `DateTimeField(default=timezone.now)` | |
| `expira_em` | `DateTimeField` | `criado_em` + 24 horas (RF-98) |
| `confirmado_em` | `DateTimeField(null=True, blank=True)` | |
| `invalidado_em` | `DateTimeField(null=True, blank=True)` | Um novo pedido invalida o anterior |

## Exceções (`contas/exceptions.py`)

| Exceção | Mensagem |
|---|---|
| `SenhaAtualIncorreta` | "Senha atual incorreta" |
| `LinkConfirmacaoInvalido` | "Link de confirmação expirado ou inválido" |
| `EmailJaCadastrado` (já existe) | "E-mail já cadastrado" |

## `PerfilService` (`contas/services/perfil.py`)

| Método | Regra |
|---|---|
| `atualizar(usuario, dados: DadosPerfil, montar_link) -> bool` | Compara cada campo com o valor gravado. Grava os campos alterados, menos o e-mail, e registra uma linha de histórico por campo (RF-103). "Qual deficiência" é apagado quando a deficiência deixa de ser "Sim, outra" (RF001). Um e-mail novo é verificado (`EmailJaCadastrado`) e gera uma `ConfirmacaoEmail`, com o link enviado ao novo endereço. Devolve se ficou um e-mail pendente (RF-98) |
| `confirmar_email(codigo) -> Usuario` | Código válido, não expirado nem usado (`LinkConfirmacaoInvalido`) e e-mail ainda livre (`EmailJaCadastrado`). Troca o e-mail, registra o histórico e, depois do commit, avisa o endereço anterior |
| `trocar_senha(usuario, senha_atual, nova_senha) -> None` | `SenhaAtualIncorreta` se a atual não confere, `SenhaIgualAAtual` se a nova é igual. Grava com `set_password` e registra o histórico só com o campo e a data (RF-102, RF-103). A view chama `update_session_auth_hash` para manter a sessão atual |
| `trocar_foto(usuario, arquivo) -> None` | Valida, grava a nova foto e apaga o arquivo anterior depois do commit (RF-100) |

`DadosPerfil` é uma dataclass imutável com nome, e-mail, telefone, deficiência, qual deficiência, contato com Libras e `receber_lembretes`.

O módulo recomendado já é calculado a partir de `contato_libras` a cada acesso à trilha, então alterar o campo atualiza a recomendação sem outra regra (RF-99).

## Forms (`contas/forms/perfil.py`)

- `PerfilForm`: os campos editáveis e `receber_lembretes`. Os campos comuns ao cadastro, com as regras e normalizações do RF001, ficam em `DadosPessoaisForm` (`contas/forms/dados_pessoais.py`), base do `CadastroForm` e do `PerfilForm`. CPF e data de nascimento aparecem só como texto.
- `FotoForm`: `foto` com o `ImagemPerfilValidator` ("Arquivo inválido. Envie uma imagem JPG ou PNG de até 2 MB").
- `TrocaSenhaForm`: `senha_atual`, `nova_senha` e `confirmacao`, com o `ValidacaoDeSenhaMixin` da spec 0011.

Os códigos dos links de uso único (RF004 e RF005) são gerados e transformados em hash por `contas/services/codigos.py`.

## Rotas (`app_name = "contas"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/perfil/` | `contas:perfil` | `PerfilView` | GET, POST | Aluno |
| `/perfil/foto/` | `contas:foto` | `FotoView` | POST | Aluno |
| `/perfil/senha/` | `contas:trocar_senha` | `TrocaSenhaView` | GET, POST | Aluno |
| `/perfil/confirmar-email/<codigo>/` | `contas:confirmar_email` | `ConfirmarEmailView` | GET | Qualquer pessoa com o link |

## Comportamento

- **`PerfilView`:**
  - GET mostra os dados.
  - POST válido mostra "Dados atualizados com sucesso" e, com e-mail novo, também "Enviamos um link de confirmação para o novo e-mail".
  - Erros aparecem nos campos, sem apagar o que foi digitado (RNF002).
  - O link Cancelar pede a confirmação do RF001 ("Deseja realmente cancelar? Os dados não salvos serão perdidos") com `confirm()`, em `static/js/perfil.js`. O `cadastro.js` também é carregado, para esconder "Qual deficiência" como no cadastro.
- **`ConfirmarEmailView`:** confirma, mostra "Dados atualizados com sucesso" e leva ao perfil, se o usuário estiver autenticado, ou ao login. Um link que não vale mais, ou um e-mail que outra conta passou a usar, mostra "Link de confirmação expirado ou inválido" com status 400.
- **`TrocaSenhaView`:** mostra "Senha alterada com sucesso" e volta ao perfil.
- O aluno só acessa os próprios dados: as views usam sempre `request.user`, sem id na rota (RF-104). O administrador recebe 403, pelo `SomenteAlunoMixin` (`contas/views/acesso.py`), também usado pelo Fale conosco.
- O menu ganha o link "Perfil" para o aluno.

## Limites aceitos nesta versão

- A foto aparece só na tela do perfil. O documento não diz onde exibi-la.
- A preferência de lembretes é gravada, mas não tem efeito até o RF011 existir.

## Testes

- [x] Cada campo alterado gera uma linha de histórico com os valores anterior e novo. A troca de senha gera uma linha sem valores.
- [x] CPF e data de nascimento não mudam, mesmo que o POST os envie.
- [x] O e-mail novo só vale depois da confirmação, o link vence em 24 horas e o endereço anterior recebe o aviso.
- [x] Um e-mail já usado é recusado ao pedir a troca e ao confirmar.
- [x] A troca de senha exige a senha atual, recusa a mesma senha e mantém a sessão atual.
- [x] A foto aceita JPG e PNG de até 2 MB pelo tipo real, recebe nome gerado e apaga a anterior.
- [x] Alterar "Teve contato com Libras" muda o módulo recomendado na trilha.
- [x] As rotas recusam visitante (login) e administrador (403).
