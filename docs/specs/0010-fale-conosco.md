# Spec 0010: Fale conosco

- **Status:** Implementado
- **Requisitos:** RF-86 a RF-91 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF020 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0003](../adr/0003-django-admin-como-area-administrativa.md), [ADR 0006](../adr/0006-estruturas-do-banco-em-sql.md), [ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)
- **Depende de:** [Spec 0003](0003-trilha.md)

O aluno envia dúvidas, sugestões e relatos de problemas e acompanha a resposta. O administrador responde pelo Admin. Pelo ADR 0009, o model é criado antes da tela, no novo app `contato`.

## Configurações e dependências

- `INSTALLED_APPS`: adicionar `"contato"`.
- `contato` depende de `contas` (o aluno, por `AUTH_USER_MODEL`) e de `trilha` (a aula relacionada). Nenhum app importa `contato`.

## Model `MensagemContato` (`contato/models/mensagem.py`)

Choices no nível do módulo, como nos outros apps:

- `AssuntoMensagem`: `DUVIDA` "Dúvida", `PROBLEMA_TECNICO` "Problema técnico", `ERRO_CONTEUDO` "Erro em conteúdo", `SUGESTAO` "Sugestão".
- `SituacaoMensagem`: `ABERTA` "Aberta", `EM_ANALISE` "Em análise", `RESOLVIDA` "Resolvida".

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `ForeignKey(AUTH_USER_MODEL, PROTECT, related_name="mensagens_contato")` | Mensagens de usuários desativados são mantidas (RF-91) |
| `assunto` | `CharField(20, choices=AssuntoMensagem)` | Obrigatório |
| `aula` | `ForeignKey(Aula, SET_NULL, null=True, blank=True, related_name="mensagens_contato")` | Opcional. Excluir a aula não apaga a mensagem |
| `mensagem` | `CharField(1000)` | De 10 a 1.000 caracteres, texto puro (RS013) |
| `situacao` | `CharField(20, choices=SituacaoMensagem, default=ABERTA)` | |
| `resposta` | `CharField(1000, blank=True)` | Texto puro (RS013) |
| `enviada_em` | `DateTimeField(default=timezone.now)` | |
| `resolvida_em` | `DateTimeField(null=True, blank=True)` | Preenchida ao marcar como Resolvida |

Constraints:

- `contato_mensagemcontato_assunto_valido` e `contato_mensagemcontato_situacao_valido`: os valores das choices, no padrão `<tabela>_<campo>_valido`.
- `mensagem_tamanho_minimo`: `CheckConstraint(condition=GreaterThanOrEqual(Length("mensagem"), 10))`.
- `mensagem_resolucao_coerente`: Resolvida tem `resolvida_em` e resposta preenchidas; as outras situações não têm `resolvida_em`.

Índices:

- `mensagem_fila_idx` (`situacao`, `enviada_em`), para a fila do Admin.
- `mensagem_aluno_data_idx` (`aluno`, `enviada_em`), para "Minhas mensagens" e o limite diário.

## Exceções (`contato/exceptions.py`)

`ErroDeContato` é a base de:

| Exceção | Mensagem |
|---|---|
| `LimiteDiarioAtingido` | "Limite de 5 mensagens por dia atingido. Tente novamente amanhã" |
| `RespostaObrigatoria` | "Informe a resposta para marcar como resolvida" |
| `MensagemJaResolvida` | "Uma mensagem resolvida não volta a outra situação" |

## `MensagemService` (`contato/services/mensagem.py`)

| Método | Regra |
|---|---|
| `aulas_disponiveis() -> list[tuple[str, list[tuple[int, str]]]]` | Aulas publicadas, agrupadas pelo título do módulo, em ordem de posição (RF-86) |
| `enviar(aluno, assunto, aula_id, mensagem) -> MensagemContato` | Conta as mensagens do aluno no dia local (`enviada_em__date`, fuso `America/Sao_Paulo`). Com 5 ou mais, levanta `LimiteDiarioAtingido` (RF-87). Grava com a situação Aberta |
| `do_aluno(aluno, pagina) -> Page` | Só as mensagens do aluno, da mais recente para a mais antiga, 20 por página (RF-88), com `select_related("aula")` |
| `validar_atualizacao(situacao_atual, nova_situacao, resposta) -> None` | Mensagem já Resolvida não volta a outra situação (`MensagemJaResolvida`). Passar a Resolvida exige resposta (`RespostaObrigatoria`) (RF-90). O `clean` do form do Admin chama este método |
| `atualizar(mensagem, situacao_anterior) -> MensagemContato` | Usado pelo `save_model` do Admin, com a situação e a resposta já preenchidas na instância. Valida de novo, tira os espaços da resposta e grava `resolvida_em` na primeira vez que a mensagem fica Resolvida |
| `fila() -> QuerySet` | Para o Admin: não resolvidas primeiro e, dentro de cada grupo, as mais antigas primeiro (RF-89) |

## Form `MensagemContatoForm` (`contato/forms/mensagem.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `assunto` | `ChoiceField` | Obrigatório |
| `aula` | `TypedChoiceField(coerce=int, empty_value=None)` | Opcional, opções de `aulas_disponiveis`, "Nenhuma" como padrão |
| `mensagem` | `CharField(min_length=10, max_length=1000, widget=Textarea)` | "A mensagem deve ter entre 10 e 1.000 caracteres". Espaços nas pontas removidos |

## Rotas (`app_name = "contato"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/fale-conosco/` | `contato:enviar` | `FaleConoscoView` | GET, POST | Aluno. Visitante vai ao login; administrador recebe 403 |
| `/fale-conosco/minhas-mensagens/` | `contato:minhas` | `MinhasMensagensView` | GET | Aluno |

## Comportamento

- **`FaleConoscoView`:**
  - GET mostra o formulário.
  - POST válido chama `enviar`, mostra "Mensagem enviada. Acompanhe a resposta em Minhas mensagens" e redireciona para `contato:minhas`.
  - `LimiteDiarioAtingido` reapresenta o formulário com a mensagem e os dados (RNF002).
- **`MinhasMensagensView`:** lista data, assunto, aula, situação em texto, mensagem e resposta. Sem mensagens, mostra "Você ainda não enviou mensagens". Não há botão de alterar nem de excluir (RF-88).
- Tudo é exibido com o escape automático dos templates (RS013).
- O menu ganha o link "Fale conosco" para o aluno.

## Admin

### `MensagemContatoAdmin`

- A listagem mostra data, nome e e-mail do aluno, assunto, aula e situação, com filtros de assunto e situação, 20 por página. A ordem vem de `MensagemService.fila()` (RF-89).
- O aluno aparece só por nome e e-mail, em campos somente leitura. CPF e deficiência nunca aparecem (RNF006).
- São editáveis só a situação e a resposta (RF-90). O `clean` do form chama `MensagemService.validar_atualizacao` e mostra as mensagens de erro, e `save_model` grava por `MensagemService.atualizar`.
- Não permite incluir nem excluir. O histórico do Admin (`LogEntry`) registra cada mudança com data, hora e autor (RF-91).

## Limites aceitos nesta versão

- Dois envios simultâneos podem passar do limite diário em uma mensagem, porque a contagem não trava a linha do aluno.
- A resposta só aparece na plataforma, sem e-mail (RF-91).

## Testes

- [x] O banco recusa assunto e situação fora das opções, mensagem com menos de 10 caracteres e Resolvida sem resposta ou sem data.
- [x] `enviar` grava a mensagem como Aberta e recusa a sexta do dia, mas aceita no dia seguinte (fuso local).
- [x] A aula relacionada só aceita aulas publicadas.
- [x] "Minhas mensagens" mostra só as mensagens do aluno, da mais recente para a mais antiga, e a mensagem de lista vazia.
- [x] `atualizar` exige resposta para Resolvida, grava a data e não deixa Resolvida voltar.
- [x] A fila do Admin põe as não resolvidas mais antigas primeiro.
- [x] O Admin não mostra CPF nem deficiência e não permite incluir nem excluir.
- [x] As rotas recusam visitante (login) e administrador (403).
- [x] Uma mensagem com `<script>` aparece escapada.
