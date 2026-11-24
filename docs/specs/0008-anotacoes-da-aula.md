# Spec 0008: Anotações da aula

- **Status:** Implementado
- **Requisitos:** RF-74 a RF-79 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF019 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)
- **Depende de:** [Spec 0003](0003-trilha.md)

O aluno guarda uma anotação pessoal por aula, na própria tela da aula. Pelo ADR 0009, o model é criado antes da tela.

## Model `AnotacaoAula` (`trilha/models/anotacao.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `ForeignKey(AUTH_USER_MODEL, PROTECT, related_name="anotacoes")` | |
| `aula` | `ForeignKey(Aula, PROTECT, related_name="anotacoes")` | Uma aula com anotação também tem progresso e já não pode ser excluída (RF013) |
| `texto` | `CharField(2000)` | Texto puro (RS013) |
| `atualizada_em` | `DateTimeField(default=timezone.now)` | Data e hora da última alteração (RF-75) |

Constraints:

- `anotacao_unica_por_aula`: `UniqueConstraint(fields=["aluno", "aula"])` (RF-75).
- `anotacao_texto_preenchido`: `CheckConstraint(condition=~Q(texto=""))`. O limite de 2.000 caracteres fica no tipo `varchar(2000)`.

## Exceção (`trilha/exceptions.py`)

| Exceção | Uso |
|---|---|
| `AcaoSomenteDoAluno(ErroDeTrilha)` | Administrador tentando gravar anotação ou avaliação. A view responde 403 |

## `AnotacaoService` (`trilha/services/anotacao.py`)

| Método | Regra |
|---|---|
| `obter(aluno, aula) -> AnotacaoAula \| None` | A anotação do aluno na aula |
| `salvar(aluno, aula_id, texto) -> AnotacaoAula` | Aplica `ExibicaoAulaService.verificar_acesso`, então aula despublicada dá `AulaNaoEncontrada`. Recusa administrador (`AcaoSomenteDoAluno`). Cria ou atualiza a anotação com `update_or_create` e grava `atualizada_em` |
| `excluir(aluno, aula_id) -> bool` | Mesmas verificações. Apaga a anotação e devolve se havia uma (RF-76) |

`AulaAberta` ganha o campo `anotacao`, preenchido por `ExibicaoAulaService.abrir` só para o aluno. Anotações de aulas despublicadas continuam gravadas e reaparecem quando a aula volta a ser publicada (RF-79), porque só o acesso à aula muda.

## Form `AnotacaoForm` (`trilha/forms/anotacao.py`)

`texto`: `CharField(max_length=2000, widget=Textarea)`, com as mensagens "Campo obrigatório não preenchido" e "A anotação deve ter até 2.000 caracteres" (RF-74). Espaços nas pontas são removidos, então um texto só de espaços conta como vazio.

## Rotas (`app_name = "trilha"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/aulas/<int:aula_id>/anotacao/` | `trilha:salvar_anotacao` | `AnotacaoView` | POST | Aluno com acesso à aula |
| `/aulas/<int:aula_id>/anotacao/excluir/` | `trilha:excluir_anotacao` | `ExcluirAnotacaoView` | POST | Aluno com acesso à aula |

## Comportamento

- **`AnotacaoView.post`:** form válido chama `salvar`, mostra "Anotação salva" e redireciona para a aula, na âncora `#anotacoes`. Form inválido reapresenta a tela da aula com o erro no campo e o texto digitado (RNF002).
- **`ExcluirAnotacaoView.post`:** chama `excluir`, mostra "Anotação excluída" e redireciona para a aula.
- Nas duas, `AulaNaoEncontrada` vira 404, o visitante vai ao login e `AcaoSomenteDoAluno` vira 403.
- **Tela da aula:**
  - O aluno vê a área "Minhas anotações" com o texto salvo, a data da última alteração e os botões Salvar e Excluir.
  - Um contador mostra os caracteres restantes, anunciado com `aria-live="polite"`.
  - O botão Excluir pede "Deseja realmente excluir esta anotação?" com `confirm()`, em `static/js/aula.js`.
  - O visitante vê "Faça login para salvar anotações" (RF-78). O administrador não vê a área (RF-77).
  - O texto é exibido com o escape automático dos templates, sem `safe` (RS013).

## Admin

Sem registro. Só o próprio aluno vê a anotação (RF-77).

## Limites aceitos nesta versão

- Sem JavaScript, o contador não aparece e a exclusão não pede confirmação.
- Duas abas salvando ao mesmo tempo: vale a última gravação.

## Testes

- [x] O banco recusa duas anotações do mesmo aluno na mesma aula e o texto vazio.
- [x] `salvar` cria e depois atualiza a mesma anotação, com a data da alteração.
- [x] `salvar` e `excluir` recusam aula não publicada, aula restrita ao visitante e administrador.
- [x] Texto com mais de 2.000 caracteres mostra a mensagem e mantém o texto.
- [x] A exclusão apaga a anotação, que não volta.
- [x] Um aluno não lê nem altera a anotação de outro.
- [x] A anotação de aula despublicada continua gravada e volta a aparecer quando a aula é publicada.
- [x] O visitante vê o aviso de login, e o administrador não vê a área.
- [x] Um texto com `<script>` aparece escapado.
