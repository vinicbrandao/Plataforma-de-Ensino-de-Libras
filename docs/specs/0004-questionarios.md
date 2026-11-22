# Spec 0004: Questionários e conclusão da aula

- **Status:** Implementado
- **Requisitos:** RF-30, RF-34 a RF-38, RF-47, RF-51, RF-52, RF-55, RF-59 e RF-60 do [PRD 0001](../prd/0001-plataforma-libras-v1.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0003](../adr/0003-django-admin-como-area-administrativa.md), [ADR 0004](../adr/0004-conclusao-da-aula-pelo-questionario.md), [ADR 0006](../adr/0006-estruturas-do-banco-em-sql.md)
- **Depende de:** [Spec 0002](0002-dicionario.md), [Spec 0003](0003-trilha.md)

Esta spec fecha o ciclo da aula: o aluno aprovado no questionário conclui a aula, e a trilha mostra o progresso.

## Configurações e dependências

- `INSTALLED_APPS`: adicionar `"questionarios"`.
- `questionarios` depende de `trilha` e de `dicionario`. Os outros dois apps não importam `questionarios`: usam apenas o nome reverso `questoes` nas consultas, como manda o `arquitetura.md`.
- O questionário fica em uma página própria, `/aulas/<id>/questionario/`, e a tela da aula leva a ela pelo botão "Responder questionário". Assim, a view da aula não importa o app de questionários.

## Models

### `Questao`

| Campo | Tipo | Regras |
|---|---|---|
| `aula` | `ForeignKey(Aula, CASCADE, related_name="questoes")` | |
| `enunciado` | `CharField(500)` | Obrigatório |
| `sinal` | `ForeignKey(Sinal, PROTECT, null=True, blank=True, related_name="questoes")` | Vídeo do sinal mostrado com o enunciado. `PROTECT` impede excluir o sinal (RF-55) |
| `posicao` | `PositiveIntegerField` | Ordem no questionário |

Constraints: `questao_posicao_unica_na_aula` (`aula` + `posicao`) e `questao_posicao_positiva`. Ordenação: `aula`, `posicao`.

### `Alternativa`

`questao` (`ForeignKey(Questao, CASCADE, related_name="alternativas")`), `texto` (`CharField(200)`) e `correta` (`BooleanField(default=False)`). Ordenação: `id`, a ordem de cadastro.

Constraint `alternativa_correta_unica`: `UniqueConstraint(fields=["questao"], condition=Q(correta=True))`. O PostgreSQL cria um índice único parcial (`CREATE UNIQUE INDEX ... WHERE correta`), que impede duas alternativas corretas na mesma questão mesmo fora da aplicação. A regra de ter exatamente uma correta e de 2 a 5 alternativas fica no service, pois depende do conjunto (ADR 0006).

### `Tentativa`

Resultado de uma tentativa do aluno. É uma fotografia do momento: guarda os números, e não as questões, para que alterar ou excluir questões não mude as tentativas registradas (RF-52).

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `ForeignKey(AUTH_USER_MODEL, PROTECT, related_name="tentativas")` | |
| `aula` | `ForeignKey(Aula, PROTECT, related_name="tentativas")` | |
| `acertos` | `PositiveSmallIntegerField` | |
| `total` | `PositiveSmallIntegerField` | |
| `percentual` | `PositiveSmallIntegerField` | Arredondado |
| `aprovada` | `BooleanField` | |
| `realizada_em` | `DateTimeField(default=timezone.now)` | Índice com `aluno` |

Constraints: `tentativa_total_positivo` (`total > 0`) e `tentativa_acertos_validos` (`acertos <= total`).

## Exceções (`questionarios/exceptions.py`)

`ErroDeQuestionario` é a base de:

| Exceção | Mensagem |
|---|---|
| `PosicaoDeQuestaoJaCadastrada` | "Posição já cadastrada para esta aula" |
| `QuantidadeDeAlternativasInvalida` | "Cadastre de 2 a 5 alternativas" |
| `AlternativaCorretaInvalida` | "Marque exatamente uma alternativa correta" |
| `UltimaQuestaoDeAulaPublicada` | "A aula publicada precisa de ao menos uma questão" |
| `RespostasIncompletas` | "Responda todas as questões antes de enviar" |

## Services

### `QuestaoService` (Admin, RF014)

| Método | Regra |
|---|---|
| `validar_posicao(aula_id, posicao, ignorar_pk)` | `PosicaoDeQuestaoJaCadastrada` |
| `validar_alternativas(corretas: list[bool])` | Recebe uma lista com uma entrada por alternativa. Exige de 2 a 5 entradas e exatamente uma verdadeira |
| `validar_exclusao(questao)` | `UltimaQuestaoDeAulaPublicada` se a aula está publicada e esta é a única questão dela |
| `salvar(questao)` | Valida a posição e grava |
| `excluir(questao)` | Chama `validar_exclusao` e exclui |

### `QuestionarioService` (aluno, RF009)

| Método | Regra |
|---|---|
| `aprovado(acertos, total)` | `acertos * 10 >= total * 7` |
| `carregar(aula_id, usuario) -> QuestionarioAberto` | Aplica `ExibicaoAulaService.verificar_acesso` e devolve a aula e as questões em ordem de posição, com `select_related("sinal")` e `prefetch_related("alternativas")` |
| `corrigir(aula_id, usuario, respostas: dict[int, int]) -> Resultado` | Aplica `verificar_acesso` de novo. Recebe um dicionário com o id da questão e o id da alternativa escolhida. Sem questões, levanta `QuestionarioSemQuestoes` ("Esta aula ainda não tem questões"). Exige uma resposta válida para cada questão (`RespostasIncompletas`). Calcula acertos, total e percentual. Aprova com `acertos * 10 >= total * 7`, ou seja, 70% sem arredondamento (RF-36). Para o aluno, grava a `Tentativa` e, na aprovação, chama `ProgressoService.concluir` (RF-30, ADR 0004). Para o visitante e o administrador, não grava nada (RF-38) |

`Resultado` é uma dataclass imutável com acertos, total, percentual, se foi aprovado, se a aula foi concluída, a próxima aula e uma `Correcao` por questão: a questão, a alternativa escolhida, a correta e se acertou.

## Mudanças na trilha (spec 0003)

- `ExibicaoAulaService.verificar_acesso(aula_id, usuario) -> Aula` aplica as regras de acesso de `abrir` sem registrar progresso, e `abrir` passa a usá-lo. O questionário usa `verificar_acesso`: o visitante só responde o questionário da primeira aula, e a aula não publicada só abre para o administrador.
- `AulaService.validar_publicacao` ganha o argumento `tem_questao`, e `AulaService.tem_questao(aula_id)` consulta `Aula.objects.filter(pk=..., questoes__isnull=False)`. A publicação passa a exigir vídeo, legenda e ao menos uma questão (RF-47). Uma aula nova é salva primeiro como não publicada, recebe as questões e só então é publicada.
- `trilha/tests/fabricas.criar_aula(publicada=True)` grava a aula pelo service sem publicar e marca a publicação por `update`. Os testes da trilha não dependem do app de questionários.

## Mudança no dicionário (spec 0002)

`SinalService.validar_inativacao(sinal_id, ativo)` levanta `SinalEmUso` ("Este sinal é usado em aulas e não pode ser inativado ou excluído") ao inativar um sinal usado em questão de aula publicada. A consulta é `Sinal.objects.filter(pk=..., questoes__aula__publicada=True)`. O form do Admin chama esse método em `clean_ativo`. A exclusão de sinal usado em questão é barrada pelo `PROTECT` (RF-55).

## Form `QuestionarioForm`

Recebe as questões e cria um campo `questao_<id>` (`ChoiceField` com `RadioSelect`, opcional) para cada uma, com as alternativas como opções. `respostas()` devolve o dicionário de questão para alternativa, só com as respondidas. A exigência de responder todas fica no service.

## Rotas (`app_name = "questionarios"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/aulas/<int:aula_id>/questionario/` | `questionarios:responder` | `QuestionarioView` | GET, POST | As mesmas regras de acesso da aula |

## Comportamento

### `QuestionarioView`

- **GET:** mostra as questões, com o vídeo do sinal quando houver. Sem questões, mostra "Esta aula ainda não tem questões". `AulaNaoEncontrada` vira 404, e `AulaRestritaAVisitante` vira a mensagem "Faça login para acessar esta aula" e o redirecionamento para o login.
- **POST:** chama `QuestionarioService.corrigir`. `RespostasIncompletas` reapresenta o form com a mensagem e as respostas marcadas (RF-35). Em caso de sucesso, mostra o resultado na própria resposta (RF-37):
  - aprovado: "Aprovado! Você acertou X de Y questões";
  - reprovado: "Você acertou X de Y questões. É necessário acertar 70% para concluir. Tente novamente";
  - o percentual e, para cada questão errada, a alternativa escolhida e a correta;
  - para o aluno aprovado: "Aula concluída!" e o link para a próxima aula;
  - botão para responder de novo.
- O resultado não usa redirecionamento após o POST porque a tentativa do visitante não é gravada, então não há o que reabrir. Reenviar o formulário só registra outra tentativa, e as tentativas são ilimitadas (RF-38).
- O visitante vê "Faça login para salvar seu progresso".

### Tela da aula

Ganha o botão "Responder questionário", que leva a `questionarios:responder`.

## Admin

### `QuestaoAdmin`

- `list_display` com aula, posição e enunciado; `list_filter` pela aula; pesquisa pelo enunciado; ordenação por aula e posição; `list_select_related`; 20 por página (RF-59).
- Alternativas em inline (`TabularInline`, `min_num=2`, `max_num=5`, `extra=0`). O formset chama `QuestaoService.validar_alternativas` com as alternativas não excluídas e mostra a mensagem acima do inline.
- O form chama `QuestaoService.validar_posicao` e mostra a mensagem no campo. `save_model` chama `QuestaoService.salvar`.
- `has_delete_permission` devolve `False` para a última questão de aula publicada. `delete_queryset` chama `QuestaoService.excluir` para cada questão e informa as que não puderam ser excluídas (RF-52).

### `TentativaAdmin`

Somente leitura, sem inclusão, alteração nem exclusão. Lista aluno, aula, acertos, total, percentual, aprovação e data. Serve de consulta para a equipe enquanto o RF012 está fora do escopo.

## Limites aceitos nesta versão

- A tentativa guarda só os números, e não as respostas escolhidas. O detalhe por questão aparece apenas logo após o envio.
- A ordem das alternativas é a de cadastro, e elas não são embaralhadas.
- A aula nova precisa ser salva duas vezes: uma para receber questões e outra para ser publicada.

## Testes

- [x] O banco recusa duas alternativas corretas na mesma questão (índice único parcial).
- [x] `validar_alternativas` exige de 2 a 5 alternativas e exatamente uma correta.
- [x] Posição de questão repetida na mesma aula é recusada, e em outra aula é aceita.
- [x] A última questão de aula publicada não é excluída, mas com outra questão na aula a exclusão funciona.
- [x] A publicação exige ao menos uma questão, pelo service e pelo Admin.
- [x] Sinal usado em questão de aula publicada não é inativado, e sinal usado em questão não é excluído.
- [x] `corrigir` recusa respostas incompletas e alternativas de outra questão.
- [x] 70% aprova e menos de 70% reprova, sem arredondar (7 de 10 aprova, 2 de 3 reprova).
- [x] O aluno aprovado tem a tentativa gravada e a aula concluída. Reprovado, só a tentativa.
- [x] Reprovar depois de aprovado não desfaz a conclusão.
- [x] O visitante responde o questionário da primeira aula sem registro, e nas outras é redirecionado.
- [x] Alterar ou excluir uma questão não muda as tentativas registradas.
- [x] A tela mostra as mensagens de aprovação, de reprovação e de respostas incompletas, e a alternativa correta das questões erradas.
- [x] Depois da aprovação, a trilha mostra a aula como Concluída e o percentual atualizado.
- [x] O Admin recusa alternativas inválidas e posição repetida com mensagem, e lista as tentativas somente para leitura.
