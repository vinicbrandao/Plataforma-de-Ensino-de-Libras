# Spec 0003: Trilha, vídeo-aula e progresso

- **Status:** Implementado
- **Requisitos:** RF-16 a RF-33, RF-45 a RF-50, RF-59 e RF-60 do [PRD 0001](../prd/0001-plataforma-libras-v1.md); RNF-02, RNF-03 e RNF-07
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0003](../adr/0003-django-admin-como-area-administrativa.md), [ADR 0007](../adr/0007-plataforma-sem-pratica-com-camera.md), [ADR 0006](../adr/0006-estruturas-do-banco-em-sql.md)
- **Depende de:** [Spec 0001](0001-fundacao-e-contas.md), [Spec 0002](0002-dicionario.md)

## Divisão com a spec 0004

- A publicação (RF-47) exige aqui vídeo e legenda. A exigência de ao menos uma questão entra na spec 0004, em `AulaService.validar_publicacao`.
- A conclusão da aula (RF-30, RF-31) fica em `ProgressoService.concluir`, implementado e testado aqui. Quem o chama é o questionário, na spec 0004. Até lá, nenhuma tela conclui aulas.

## Configurações e estrutura

- `INSTALLED_APPS`: adicionar `"trilha"`.
- A rota `inicio` passa de `contas.InicioView` para `trilha.TrilhaView`. `contas/views/inicio.py` e `contas/templates/contas/inicio.html` são removidos.
- Os validadores de arquivo saem de `dicionario/validadores.py` e vão para `core/validadores.py`, porque a trilha também os usa e não depende do dicionário. `core` continua sem regra de negócio. A migração `dicionario/0001` passa a importar de `core.validadores`, sem mudar o esquema.

## Validadores de arquivo (`core/validadores.py`)

`ArquivoValidator` é a base: confere o tamanho máximo e chama `conteudo_valido(cabecalho)`, que cada subclasse implementa a partir dos primeiros bytes do arquivo (RS012). A mensagem é "Arquivo inválido: envie <descrição> de até <N> MB".

| Classe | Conteúdo aceito | Limite |
|---|---|---|
| `VideoMp4Validator` | Caixa `ftyp` nos bytes 4 a 8 | 20 MB nos sinais. Nas aulas, o limite é 200 MB, decisão da equipe: o RF013 não fixa um valor |
| `LegendaVttValidator` | Começa com `WEBVTT`, com ou sem BOM UTF-8 | 2 MB |
| `MaterialValidator` | PDF (`%PDF`), JPG (`FF D8 FF`) ou PNG (`89 50 4E 47`) | 10 MB (RF013 ⁷) |

## Models

### `Modulo`

| Campo | Tipo | Regras |
|---|---|---|
| `titulo` | `CharField(100)` | Gravado sem espaços repetidos |
| `descricao` | `CharField(500)` | Obrigatório |
| `posicao` | `PositiveIntegerField` | Ordem na trilha |

Constraints: `modulo_titulo_unico` (`Lower(titulo)` único), `modulo_posicao_unica` e `modulo_posicao_positiva` (`posicao > 0`). Ordenação: `posicao`.

### `Aula`

| Campo | Tipo | Regras |
|---|---|---|
| `modulo` | `ForeignKey(Modulo, PROTECT, related_name="aulas")` | `PROTECT` impede excluir módulo com aulas (RF-49) |
| `titulo` | `CharField(100)` | Gravado sem espaços repetidos |
| `descricao` | `CharField(500)` | Obrigatório |
| `posicao` | `PositiveIntegerField` | Ordem dentro do módulo |
| `video` | `FileField(upload_to="aulas/videos/<uuid>.mp4", blank=True)` | `VideoMp4Validator(200 MB)` |
| `legenda` | `FileField(upload_to="aulas/legendas/<uuid>.vtt", blank=True)` | `LegendaVttValidator` |
| `texto_apoio` | `CharField(2000, blank=True)` | |
| `publicada` | `BooleanField(default=False)` | Situação |

Constraints: `aula_titulo_unico_no_modulo` (`modulo` + `Lower(titulo)`), `aula_posicao_unica_no_modulo`, `aula_posicao_positiva` e `aula_publicada_completa` (publicada só com `video` e `legenda` preenchidos). Ordenação: `modulo__posicao`, `posicao`.

### `MaterialComplementar`

`aula` (`ForeignKey(Aula, CASCADE, related_name="materiais")`), `titulo` (`CharField(100)`) e `arquivo` (`FileField(upload_to="aulas/materiais/<uuid>.<ext>")`, com `MaterialValidator`). A extensão gravada vem do tipo detectado, e não do nome enviado. O título também é o texto alternativo das imagens (RNF-02).

### `ProgressoAula`

A ausência de registro significa Não iniciada.

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `ForeignKey(AUTH_USER_MODEL, PROTECT, related_name="progressos")` | |
| `aula` | `ForeignKey(Aula, PROTECT, related_name="progressos")` | `PROTECT` impede excluir aula com progresso (RF-49) |
| `status` | `CharField(20, choices=Status)` | `EM_ANDAMENTO` ou `CONCLUIDA` |
| `iniciada_em` | `DateTimeField(default=timezone.now)` | RF-29 |
| `ultimo_acesso_em` | `DateTimeField(default=timezone.now)` | Usado pelo botão Continuar (RF-22) |
| `concluida_em` | `DateTimeField(null=True, blank=True)` | Preenchido pela trigger |

Constraints: `progresso_unico_por_aula` (`aluno` + `aula`) e `progresso_conclusao_coerente` (`concluida_em` preenchido se, e somente se, `status = CONCLUIDA`).

**Trigger `trg_progresso_conclusao`** (`BEFORE INSERT OR UPDATE`, função `trilha_progresso_conclusao()`, criada por `RunSQL` com `reverse_sql`):

1. Se o registro era `CONCLUIDA` e passaria a outro status, levanta erro com `ERRCODE = 'check_violation'`. Esse erro chega ao Django como `IntegrityError` (RF-31).
2. Se o registro era `CONCLUIDA`, mantém o `concluida_em` original.
3. Se passa a `CONCLUIDA` sem data, preenche `concluida_em = now()` (RF-30).

Como a trigger roda antes da verificação das constraints, `progresso_conclusao_coerente` vale depois do preenchimento.

### View `vw_progresso_modulo` e model `ProgressoModulo`

Criada por `RunSQL` com `reverse_sql`. Ela tem uma linha por aluno (não administrador) e por módulo com aulas publicadas:

| Coluna | Cálculo |
|---|---|
| `aluno_id`, `modulo_id` | Chave composta |
| `aulas_publicadas` | Aulas publicadas do módulo |
| `aulas_concluidas` | Dessas, as concluídas pelo aluno |
| `percentual` | `round(100.0 * concluidas / publicadas)`, inteiro (RF-20) |

`ProgressoModulo` é o model não gerenciado (`managed = False`, `db_table = "vw_progresso_modulo"`), com `pk = CompositePrimaryKey("aluno", "modulo")`. Como a view só conta aulas publicadas, publicar ou despublicar uma aula recalcula os percentuais sem apagar conclusões (RF-23).

## Exceções (`trilha/exceptions.py`)

`ErroDeTrilha` é a base de `TituloJaCadastrado`, `PosicaoJaCadastrada`, `AulaIncompletaParaPublicar`, `AulaNaoEncontrada` e `AulaRestritaAVisitante`. As três primeiras têm o atributo `mensagem`: "Título já cadastrado", "Posição já cadastrada" e "A aula precisa de vídeo, legenda e questões para ser publicada".

## Services

### `ConteudoOrdenadoService` (base)

Base de `ModuloService` e `AulaService`, que têm título e posição únicos dentro de um escopo (a trilha inteira ou o módulo). As subclasses definem `modelo` e `escopo(objeto)`.

| Método | Regra |
|---|---|
| `normalizar_titulo(titulo)` | Tira os espaços das pontas e junta os repetidos |
| `validar_titulo(titulo, escopo, ignorar_pk)` | `TituloJaCadastrado` se outro registro do escopo tiver o mesmo título, sem diferenciar maiúsculas (RF-45, RF-46) |
| `validar_posicao(posicao, escopo, ignorar_pk)` | `PosicaoJaCadastrada` se a posição já for usada no escopo |
| `validar_regras(objeto)` | Gancho das subclasses |
| `salvar(objeto)` | Normaliza o título, valida tudo e grava em `transaction.atomic()`. Em caso de `IntegrityError`, repete as validações para levantar a exceção certa |

### `ModuloService` e `AulaService`

- `ModuloService`: escopo vazio (a trilha inteira).
- `AulaService`: escopo `{"modulo_id": ...}`.
  - `validar_publicacao(publicada, tem_video, tem_legenda)` levanta `AulaIncompletaParaPublicar` (RF-47) e é chamado por `validar_regras`.

A tela da aula usa outro service, `ExibicaoAulaService` (veja abaixo), para que o cadastro e a exibição tenham responsabilidades separadas.

### `ProgressoService`

| Método | Regra |
|---|---|
| `registrar_acesso(aluno, aula)` | Cria o progresso `EM_ANDAMENTO` na primeira abertura (RF-29) ou atualiza `ultimo_acesso_em`. Não altera aulas concluídas |
| `concluir(aluno, aula) -> ProgressoAula` | Marca `CONCLUIDA` e relê `concluida_em`, preenchido pela trigger. Chamar de novo não muda nada (RF-31) |

### `TrilhaService`

| Método | Regra |
|---|---|
| `aula_liberada_ao_visitante()` | Primeira aula publicada do primeiro módulo exibido, ou `None` |
| `ordem_recomendada(contato_libras, total_de_modulos)` | `NUNCA` e `POUCOS_SINAIS` → 1, `BASICO` → 2, `EXPERIENTE` → 3. O número é a ordem do módulo na trilha exibida, limitado à quantidade de módulos (RF-21) |
| `montar(usuario) -> Trilha` | Módulos com aulas publicadas, em ordem, com as aulas publicadas de cada um (RF-16). Para cada aula: status do aluno e se está liberada. O visitante só tem a aula do visitante liberada (RF-17), e o aluno e o administrador têm todas (RF-18). Para o aluno, também: percentual, concluídas e publicadas de cada módulo, lidos de `ProgressoModulo`; totais do curso; módulo recomendado; e a aula do botão Continuar. Usa uma consulta para os módulos com `prefetch_related`, uma para os progressos e uma para a view |
| `aula_para_continuar(...)` | A aula `EM_ANDAMENTO` com o `ultimo_acesso_em` mais recente. Sem ela, a primeira aula não concluída do módulo recomendado; depois, a primeira não concluída da trilha (RF-22) |

`Trilha`, `ModuloNaTrilha` e `AulaNaTrilha` são dataclasses imutáveis, sem acesso ao banco.

### `ExibicaoAulaService.abrir(aula_id, usuario) -> AulaAberta`

- A aula não existe, ou não está publicada e o usuário não é administrador: `AulaNaoEncontrada`. O administrador abre aulas não publicadas para conferir (RF-48).
- O visitante abre só a aula liberada ao visitante. As demais levantam `AulaRestritaAVisitante` (RF-17).
- Para o aluno, chama `ProgressoService.registrar_acesso`. Para o visitante e o administrador, nada é registrado (RF-32).
- `AulaAberta` traz a aula, os materiais, o status, a próxima aula da trilha (a seguinte no módulo ou a primeira do próximo módulo) e `legenda_ativa`, verdadeiro para o aluno com `deficiencia = AUDITIVA` (RF-27).

## Rotas

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/` | `inicio` | `TrilhaView` | GET | Público |
| `/aulas/<int:aula_id>/` | `trilha:aula` | `AulaView` | GET | Público, com as regras de `abrir` |

## Comportamento

### `TrilhaView`

- Mostra os módulos e as aulas. Cada aula do aluno exibe o status em texto, com ícone e cor (RF-19).
- Aula bloqueada para o visitante: aparece com a indicação "faça login" e leva à aula, que redireciona para o login.
- Para o aluno: barra de progresso (`<progress>`) e texto "7 de 20 aulas · 35%" em cada módulo e no curso (RF-20), destaque "Comece pelo Módulo X!" no módulo recomendado (RF-21) e botão Continuar (RF-22).
- Sem módulos publicados, exibe "Nenhuma aula publicada ainda".

### `AulaView`

- `AulaNaoEncontrada` vira `Http404`. `AulaRestritaAVisitante` vira a mensagem "Faça login para acessar esta aula" e um redirecionamento para o login com `next`.
- O vídeo usa `<video controls preload="metadata">`, que começa pausado, com `<track kind="subtitles" srclang="pt-BR" label="Português">`, que recebe o atributo `default` quando `legenda_ativa`. Os controles nativos funcionam pelo teclado (RF-25 a RF-27).
- Se o vídeo não carregar, `static/js/aula.js` mostra "Não foi possível carregar o vídeo. Tente novamente" e um botão que chama `video.load()` (RF-33).
- Exibe o texto de apoio e os materiais: imagens com `alt` igual ao título e links para abrir e baixar (RF-28).
- O visitante vê "Faça login para salvar seu progresso" (RF-32).
- Com a aula concluída: "Aula concluída!" e o link para a próxima aula (RF-30).

## Admin

- **`ModuloAdmin`:** `list_display` com posição e título, ordenado por posição, com pesquisa por título e 20 por página. O form valida título e posição pelo `ModuloService`, com a mensagem no campo, e `save_model` chama `ModuloService.salvar`.
- **`AulaAdmin`:**
  - `list_display` com módulo, posição, título e situação; `list_filter` por módulo e situação; pesquisa por título; `list_select_related`; 20 por página.
  - O form valida título, posição e publicação pelo `AulaService`, com a mensagem no campo, e `save_model` chama `AulaService.salvar`.
  - Materiais em inline (`TabularInline`).
  - `view_on_site` leva à tela da aula, que o administrador abre mesmo sem publicação (RF-48).
- **Exclusões:** módulo com aulas e aula com progresso são barrados pelo `PROTECT`, e o Admin lista os registros que impedem a exclusão. A aula com progresso continua podendo ser despublicada (RF-49).
- As listagens ficam ordenadas por posição, e o `LogEntry` registra as alterações (RF-59, RF-60).

## Limites aceitos nesta versão

- Não há retomada do vídeo nem qualidade adaptativa (simplificação do PRD).
- Arquivos substituídos ou de registros excluídos continuam no disco.
- As mensagens de exclusão barrada são as do Admin, e não as do RF013 (ADR 0003).

## Testes

- [x] Os validadores aceitam os formatos corretos e recusam assinatura falsa ou tamanho acima do limite.
- [x] Título repetido sem diferenciar maiúsculas e posição repetida são recusados no módulo e na aula. Na aula, o escopo é o módulo.
- [x] Os espaços repetidos do título são removidos ao gravar.
- [x] Aula sem vídeo ou sem legenda não é publicada, nem pelo service nem pelo banco.
- [x] A trigger preenche `concluida_em` e impede voltar de Concluída. `concluir` é idempotente e mantém a data original.
- [x] A view calcula publicadas, concluídas e percentual arredondado, e despublicar uma aula recalcula sem apagar conclusões.
- [x] Módulo com aulas e aula com progresso não são excluídos (`PROTECT`).
- [x] A trilha mostra só aulas publicadas, oculta módulos sem elas e ordena por posição.
- [x] O visitante só abre a primeira aula, e as outras redirecionam para o login com a mensagem.
- [x] Abrir a aula cria o progresso Em andamento para o aluno, mas não para o visitante nem para o administrador.
- [x] A recomendação segue a resposta "Teve contato com Libras", e Continuar segue a ordem do RF-22.
- [x] A legenda começa ativada para quem informou deficiência auditiva.
- [x] Aula não publicada dá 404 ao aluno e abre para o administrador.
- [x] A montagem da trilha usa um número fixo de consultas (`assertNumQueries`).
- [x] O Admin recusa título e posição repetidos e a publicação incompleta, com mensagem no campo.
