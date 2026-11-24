# Spec 0001: Fundação e contas

> **Atualização de 24/11/2026:** o bloqueio de menores (RF-61) foi substituído pelo cadastro com responsável legal ([spec 0013](0013-cadastro-de-menor-de-idade.md)).

- **Status:** Implementado
- **Requisitos:** RF-01 a RF-15, RF-44, RF-56 a RF-61 (parte de contas), RNF-01, RNF-04, RNF-05 e RNF-06 do [PRD 0001](../prd/0001-plataforma-libras-v1.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0002](../adr/0002-postgresql-como-banco-de-dados.md), [ADR 0003](../adr/0003-django-admin-como-area-administrativa.md)

Esta spec é implementada primeiro. O modelo de usuário precisa existir antes do primeiro `migrate`.

## Configurações (`core/settings.py`)

| Configuração | Valor |
|---|---|
| `INSTALLED_APPS` | Adicionar `"contas"` |
| `AUTH_USER_MODEL` | `"contas.Usuario"` |
| `AUTHENTICATION_BACKENDS` | `["contas.backends.EmailOuCpfBackend"]` |
| `LOGIN_URL` | `"contas:entrar"` |
| `LOGIN_REDIRECT_URL` | `"inicio"` |
| `SESSION_COOKIE_AGE` | `1800` (30 minutos) |
| `SESSION_SAVE_EVERY_REQUEST` | `True`, para que os 30 minutos contem a partir da última requisição (RS010) |
| `MIDDLEWARE` | Adicionar `contas.middleware.SemCacheParaAutenticadosMiddleware` depois de `AuthenticationMiddleware` |
| `AUTH_PASSWORD_VALIDATORS` | Manter os do Django e adicionar `contas.validadores.LetrasENumerosValidator` |

## Estrutura

```text
contas/
  models/        usuario.py, falha_login.py, registro_auditoria.py
  services/      cadastro.py, autenticacao.py, usuarios.py, auditoria.py
  views/         inicio.py, cadastro.py, entrar.py, sair.py
  forms/         cadastro.py, entrar.py
  templates/contas/
  templates/admin/contas/usuario/confirmar_desativacao.html
  tests/
  documentos.py  value objects Cpf e Telefone
  validadores.py LetrasENumerosValidator
  backends.py    EmailOuCpfBackend
  middleware.py  SemCacheParaAutenticadosMiddleware
  receptores.py  registro de login e logout de administradores
  exceptions.py
  admin.py
  urls.py
templates/base.html
static/css/site.css
static/js/cadastro.js
```

## Value objects (`contas/documentos.py`)

| Classe | Regra |
|---|---|
| `Cpf.de_texto(texto)` | Aceita com ou sem pontuação. Exige 11 dígitos, rejeita sequências repetidas (`111.111.111-11`) e confere os dois dígitos verificadores. Levanta `ValueError` se for inválido |
| `Cpf.formatado` | `XXX.XXX.XXX-XX` |
| `Cpf.parcial` | `***.456.789-**`, usado no Admin (RF-56) |
| `Telefone.de_texto(texto)` | Aceita com ou sem máscara. Exige 11 dígitos, DDD de 11 a 99 e o terceiro dígito igual a 9 (celular). Levanta `ValueError` se for inválido |
| `Telefone.formatado` | `(XX) 9XXXX-XXXX` |

## Modelo `Usuario`

Herda de `AbstractBaseUser` e `PermissionsMixin`, com `USERNAME_FIELD = "email"` e `REQUIRED_FIELDS = ["nome_completo"]`. O gerenciador `UsuarioManager` grava o e-mail em minúsculas em `create_user` e `create_superuser`.

| Campo | Tipo | Regras |
|---|---|---|
| `nome_completo` | `CharField(120)` | Obrigatório |
| `email` | `EmailField(200)` | Único, sempre em minúsculas |
| `cpf` | `CharField(14, null=True, blank=True)` | Único. Nulo apenas para administradores, que não se cadastram pela tela pública. `null` permite vários administradores sem CPF sem violar a unicidade |
| `data_nascimento` | `DateField(null=True, blank=True)` | Obrigatório para alunos |
| `telefone` | `CharField(15, blank=True)` | Obrigatório para alunos |
| `deficiencia` | `CharField(20, choices=Deficiencia, blank=True)` | `NAO`, `AUDITIVA`, `VISUAL`, `OUTRA`, `NAO_INFORMAR` |
| `qual_deficiencia` | `CharField(120, blank=True)` | Preenchido somente quando `deficiencia = OUTRA` |
| `contato_libras` | `CharField(20, choices=ContatoLibras, blank=True)` | `NUNCA`, `POUCOS_SINAIS`, `BASICO`, `EXPERIENTE` |
| `termos_aceitos_em` | `DateTimeField(null=True, blank=True)` | Data e hora do aceite (RF-06) |
| `is_active` | `BooleanField(default=True)` | Situação Ativo ou Inativo (RF016) |
| `is_staff` | `BooleanField(default=False)` | Administrador (ADR 0003) |
| `data_cadastro` | `DateTimeField(default=timezone.now)` | |

Constraints:

- `usuario_email_minusculo`: `email = Lower(email)`. Junto com `unique`, impede e-mails que diferem só em maiúsculas.
- `usuario_cpf_formatado`: `cpf IS NULL` ou `cpf` no formato `^\d{3}\.\d{3}\.\d{3}-\d{2}$`.
- `usuario_aluno_completo`: `is_staff` ou todos os dados de aluno preenchidos (`cpf`, `data_nascimento`, `termos_aceitos_em` não nulos; `telefone`, `deficiencia` e `contato_libras` não vazios).
- `usuario_qual_deficiencia`: `qual_deficiencia` vazio, ou `deficiencia = OUTRA`.

Ordenação padrão: `nome_completo`.

## Modelo `FalhaLogin` (RS001)

| Campo | Tipo | Regras |
|---|---|---|
| `chave` | `CharField(64, unique)` | HMAC-SHA256 do login normalizado (`salted_hmac`). O login digitado não é guardado, pois pode ser o CPF ou o e-mail de outra pessoa (LGPD) |
| `falhas` | `PositiveSmallIntegerField(default=0)` | Falhas consecutivas |
| `bloqueado_ate` | `DateTimeField(null=True)` | |

## Modelo `RegistroAuditoria` (RS004, RS009)

| Campo | Tipo | Regras |
|---|---|---|
| `autor` | `ForeignKey(Usuario, PROTECT, related_name="registros_feitos")` | Quem fez a ação |
| `acao` | `CharField(20, choices=Acao)` | `LOGIN_ADMIN`, `LOGOUT_ADMIN`, `CONSULTA_ALUNO`, `DESATIVACAO`, `REATIVACAO` |
| `alvo` | `ForeignKey(Usuario, PROTECT, null=True, related_name="registros_recebidos")` | Aluno afetado, quando houver |
| `criado_em` | `DateTimeField(auto_now_add=True)` | Índice |

As inclusões, alterações e exclusões feitas no Admin continuam no `LogEntry` do Django (RF-60).

## Exceções (`contas/exceptions.py`)

`ErroDeContas` é a base de `EmailJaCadastrado`, `CpfJaCadastrado`, `CadastroDeMenorIndisponivel`, `CredenciaisInvalidas`, `LoginBloqueado`, `UsuarioDesativado` e `UsuarioNaoEncontrado`.

## Services

### `CadastroService`

| Método | Regra |
|---|---|
| `calcular_idade(nascimento, hoje)` | Anos completos. A idade é completa no dia do aniversário. Quem nasceu em 29/02 completa anos em 01/03 nos anos não bissextos |
| `cadastrar(dados: DadosCadastro) -> Usuario` | Para menores de 18 anos em `timezone.localdate()`, exige e grava o responsável legal ([spec 0013](0013-cadastro-de-menor-de-idade.md)); antes disso, recusava com `CadastroDeMenorIndisponivel` (RF-61). Levanta `EmailJaCadastrado` ou `CpfJaCadastrado` se já existirem (RF-04). Cria o aluno com `create_user`, `termos_aceitos_em = timezone.now()` e `is_staff = False`, dentro de `transaction.atomic()`. Se a gravação falhar por `IntegrityError` (dois cadastros simultâneos), repete a verificação e levanta a exceção de duplicidade correspondente |

`DadosCadastro` é uma dataclass imutável com os campos já validados e normalizados pelo form: e-mail em minúsculas, CPF e telefone formatados e `qual_deficiencia` vazio quando a resposta não é `OUTRA`.

### `AutenticacaoService`

| Método | Regra |
|---|---|
| `normalizar_login(login)` | Com "@": sem espaços e em minúsculas. Sem "@": se tiver 11 dígitos, CPF formatado. Senão, o texto sem espaços, que não corresponde a ninguém |
| `autenticar(login, senha) -> Usuario` | 1. Se a chave do login estiver bloqueada, levanta `LoginBloqueado`, sem conferir a senha. 2. Busca o usuário pelo e-mail ou pelo CPF. Sem usuário, roda o hasher de senha mesmo assim, para não revelar pelo tempo de resposta que o login não existe. 3. Com a senha errada, registra a falha e levanta `CredenciaisInvalidas`. 4. Com a senha certa, apaga as falhas da chave. 5. Se o usuário estiver inativo, levanta `UsuarioDesativado` (RF-11). 6. Devolve o usuário |
| `registrar_falha(chave)` | Em `transaction.atomic()` com `select_for_update`. Se o bloqueio anterior já expirou, zera o contador. Soma 1 e, ao chegar a 5, define `bloqueado_ate = agora + 15 minutos` (RS001) |

A 5ª falha ainda mostra "Login ou senha inválidos". A partir da 6ª tentativa, aparece a mensagem de bloqueio.

### `UsuarioService` (Admin de usuários, RF016)

| Método | Regra |
|---|---|
| `alunos()` | QuerySet dos usuários com `is_staff = False`, ordenado por nome |
| `buscar_alunos(queryset, termo)` | Se o termo, sem pontuação, for um CPF válido, filtra pelo CPF exato. Senão, filtra por parte do nome ou do e-mail, sem distinguir maiúsculas |
| `desativar(aluno, por)` | Marca `is_active = False` e registra `DESATIVACAO`. Não age sobre administradores (`UsuarioNaoEncontrado`) |
| `reativar(aluno, por)` | Marca `is_active = True` e registra `REATIVACAO`. O progresso é mantido |

A sessão do aluno desativado termina na requisição seguinte: o `ModelBackend` não devolve usuários inativos em `get_user`, então o aluno passa a ser tratado como visitante (RF-58).

### `AuditoriaService`

| Método | Regra |
|---|---|
| `registrar(autor, acao, alvo=None)` | Cria um `RegistroAuditoria` |

## Backend (`contas/backends.py`)

`EmailOuCpfBackend` herda de `ModelBackend`. `authenticate(request, username, password)` chama `AutenticacaoService.autenticar` e devolve `None` em caso de `CredenciaisInvalidas`, `LoginBloqueado` ou `UsuarioDesativado`. Assim, o login do Admin também aceita e-mail ou CPF e respeita o bloqueio.

## Receptores (`contas/receptores.py`)

Os sinais `user_logged_in` e `user_logged_out` registram `LOGIN_ADMIN` e `LOGOUT_ADMIN` quando o usuário é administrador (RNF-06). São conectados em `ContasConfig.ready()`. Usamos sinais aqui porque o login do Admin é uma view do Django: eles apenas chamam `AuditoriaService.registrar`, sem regra de negócio.

## Middleware

`SemCacheParaAutenticadosMiddleware` aplica `add_never_cache_headers` às respostas de usuários autenticados, para que o botão Voltar não volte a exibir telas autenticadas depois de sair (RF-15).

## Forms

### `CadastroForm` (`forms.Form`)

Todos os campos obrigatórios usam a mensagem "Campo obrigatório não preenchido".

| Campo | Validação | Mensagem |
|---|---|---|
| `nome_completo` | Remove espaços extras. De 3 a 120 caracteres, só letras (com acentos), espaço, apóstrofo e hífen | "Nome inválido" |
| `email` | Até 200 caracteres, formato `texto@texto.texto`, convertido para minúsculas | "E-mail inválido" |
| `cpf` | `Cpf.de_texto` | "CPF inválido" |
| `senha` | `validate_password`, com o `LetrasENumerosValidator` | "A senha deve ter ao menos 8 caracteres, com letras e números" |
| `confirmacao_senha` | Igual à senha | "As senhas informadas não coincidem" |
| `data_nascimento` | Não futura e no máximo 120 anos atrás | "Data de nascimento inválida" |
| `telefone` | `Telefone.de_texto` | "Telefone inválido" |
| `deficiencia` | `RadioSelect` com as 5 opções | |
| `qual_deficiencia` | Até 120 caracteres. Obrigatório com `OUTRA`. É descartado nas outras opções | "Campo obrigatório não preenchido" |
| `contato_libras` | `RadioSelect` com as 4 opções | |
| `aceite_termos` | `BooleanField` obrigatório | "É necessário aceitar os termos de uso e a política de privacidade" |

`dados()` devolve um `DadosCadastro`.

### `EntrarForm` (`forms.Form`)

`login` (até 200 caracteres) e `senha` (`PasswordInput`), ambos obrigatórios.

## Validador de senha

`LetrasENumerosValidator` exige ao menos uma letra e um dígito. A mensagem é a do RF001.

## Rotas

`core/urls.py` inclui `contas.urls` na raiz.

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/` | `inicio` | `InicioView` | GET | Público |
| `/cadastro/` | `contas:cadastro` | `CadastroView` | GET, POST | Visitante |
| `/entrar/` | `contas:entrar` | `EntrarView` | GET, POST | Visitante |
| `/sair/` | `contas:sair` | `SairView` | POST | Autenticado |

`InicioView` é provisória. A spec da trilha passa a rota `inicio` para a trilha (RF-12).

## Comportamento

### `CadastroView`

- **GET:** quem já está autenticado vai para `inicio`. Os demais veem o form, com os termos de uso completos em um bloco expansível antes do aceite.
- **POST inválido:** exibe o form novamente com as mensagens junto aos campos, mantendo os dados digitados, exceto as senhas (RNF-01).
- **POST válido:** chama `CadastroService.cadastrar`. `EmailJaCadastrado` e `CpfJaCadastrado` viram erro no campo correspondente. `CadastroDeMenorIndisponivel` vira erro em `data_nascimento`: "O cadastro de menores de 18 anos ainda não está disponível". Em caso de sucesso, faz `login()`, exibe "Cadastro realizado com sucesso" e redireciona para `inicio`.
- `static/js/cadastro.js` mostra o campo "Qual deficiência" somente com "Sim, outra" e o esvazia ao trocar de opção. Sem JavaScript, o campo fica sempre visível, e o servidor aplica a mesma regra.

### `EntrarView`

- **GET:** quem já está autenticado vai para `inicio`. O `next` vem por GET, é validado com `url_has_allowed_host_and_scheme` e é repassado ao POST em um campo oculto.
- **POST:** chama `AutenticacaoService.autenticar`. As mensagens de erro, fora dos campos, são: `CredenciaisInvalidas` → "Login ou senha inválidos"; `LoginBloqueado` → "Muitas tentativas de acesso. Tente novamente em 15 minutos"; `UsuarioDesativado` → "Usuário desativado". Em caso de sucesso, chama `login(request, usuario, backend=...)` e redireciona para o `next` seguro, ou para `admin:index` se for administrador, ou para `inicio`.

### `SairView`

- **POST:** `logout(request)` e redireciona para `contas:entrar`. GET devolve 405.

### Layout base (`templates/base.html`)

`<html lang="pt-br">`, meta `viewport`, link para pular para o conteúdo, cabeçalho com o nome da plataforma e menu. Para visitantes, o menu mostra "Entrar" e "Criar conta". Para usuários autenticados, mostra o nome, "Área administrativa" para administradores e o botão "Sair" em um form POST com `{% csrf_token %}`. Tem a área de mensagens e os blocos `title` e `content`. O CSS é responsivo a partir de 360 px e tem foco visível (RNF-02, RNF-03).

## Admin

### `UsuarioAdmin` (RF016)

- `get_queryset` usa `UsuarioService.alunos()`: administradores não aparecem.
- `list_display`: nome, e-mail, CPF parcial, data de nascimento, data de cadastro e situação. `list_filter`: `is_active`. `search_fields`: nome e e-mail. `get_search_results` usa `UsuarioService.buscar_alunos`, que também aceita o CPF completo. `list_per_page = 20`.
- O detalhe mostra os mesmos campos, todos somente leitura. `deficiencia` e `qual_deficiencia` nunca são exibidos (RNF-04).
- `change_view` registra `CONSULTA_ALUNO` a cada abertura do detalhe.
- Sem inclusão nem exclusão (`has_add_permission` e `has_delete_permission` devolvem `False`). A ação em massa padrão de exclusão é removida.
- Ações "Desativar usuários selecionados" e "Reativar usuários selecionados". A desativação mostra uma página de confirmação com "Deseja realmente desativar este usuário?" e os botões Sim e Não. Ao confirmar, chama `UsuarioService.desativar` e exibe "Usuário desativado com sucesso". A reativação chama `UsuarioService.reativar` e exibe "Usuário reativado com sucesso".

### `RegistroAuditoriaAdmin`

Somente leitura, sem inclusão, alteração nem exclusão. Lista data, autor, ação e alvo, com filtro por ação.

## Limites aceitos nesta versão

- As contas de administrador são criadas com `createsuperuser`. O Admin não cria nem edita administradores.
- Não há opção de exibir a senha digitada (RF001 ⁶). As máscaras de CPF e telefone são aplicadas ao salvar, e não durante a digitação.
- A tela de login não tem "Esqueci minha senha", que depende do RF004 (bônus).
- Os termos de uso exibidos são provisórios até a equipe ter o texto final.
- Mudar `DJANGO_SECRET_KEY` invalida as chaves de `FalhaLogin`, o que zera os bloqueios em andamento.

## Testes

- [x] `Cpf` aceita CPF válido com e sem pontuação e rejeita dígito verificador errado, sequência repetida e tamanho errado.
- [x] `Cpf.parcial` e `Telefone.formatado` geram os formatos esperados. `Telefone` rejeita número que não é de celular.
- [x] `calcular_idade` considera a idade completa no dia do aniversário e trata 29/02.
- [x] `CadastroService.cadastrar` cria o aluno com o e-mail em minúsculas e registra o aceite dos termos.
- [x] `CadastroService.cadastrar` recusa e-mail repetido com maiúsculas diferentes e CPF repetido.
- [x] `CadastroService.cadastrar` recusa quem tem 17 anos e aceita quem completa 18 hoje.
- [x] O banco recusa um aluno sem CPF e um e-mail com maiúsculas (constraints).
- [x] O form de cadastro mostra a mensagem de cada campo inválido e exige "Qual deficiência" só com "Sim, outra".
- [x] O form de cadastro recusa senha sem número e senhas diferentes.
- [x] POST válido em `/cadastro/` cria a conta, autentica e redireciona para `inicio`.
- [x] `autenticar` aceita e-mail com maiúsculas e CPF com ou sem pontuação.
- [x] `autenticar` usa a mesma mensagem para login inexistente e senha errada.
- [x] Depois de 5 falhas, a 6ª tentativa é bloqueada mesmo com a senha certa, inclusive para login inexistente. Depois de 15 minutos, volta a aceitar.
- [x] Um login bem-sucedido zera as falhas.
- [x] Usuário inativo com senha certa recebe "Usuário desativado". Com senha errada, recebe "Login ou senha inválidos".
- [x] `next` interno é respeitado, `next` externo é ignorado, e administrador vai para o Admin.
- [x] Tela restrita sem autenticação redireciona para o login.
- [x] POST em `/sair/` encerra a sessão, e GET devolve 405.
- [x] Respostas para usuários autenticados têm `Cache-Control: no-store`. Respostas para visitantes não têm.
- [x] A sessão é configurada para expirar após 30 minutos de inatividade.
- [x] O Admin de usuários lista só alunos, mostra o CPF parcial, não mostra a deficiência e não permite incluir nem excluir.
- [x] A pesquisa do Admin encontra o aluno pelo CPF completo, com e sem pontuação.
- [x] Abrir o detalhe de um aluno no Admin registra `CONSULTA_ALUNO`.
- [x] A desativação pede confirmação, desativa, registra `DESATIVACAO` e encerra a sessão do aluno. A reativação registra `REATIVACAO`.
- [x] O login de um administrador registra `LOGIN_ADMIN`, e o logout registra `LOGOUT_ADMIN`.
- [x] Toda classe terminada em `View` herda diretamente de `django.views.View`, e toda rota fora do Admin aponta para uma view criada com `as_view()`.
