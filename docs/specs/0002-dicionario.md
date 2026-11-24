# Spec 0002: Dicionário de sinais

- **Status:** Implementado
- **Requisitos:** RF-39 a RF-43, RF-53, RF-54, RF-59 e RF-60 do [PRD 0001](../prd/0001-plataforma-libras-v1.md); RNF-07
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0002](../adr/0002-postgresql-como-banco-de-dados.md), [ADR 0003](../adr/0003-django-admin-como-area-administrativa.md)
- **Depende de:** [Spec 0001](0001-fundacao-e-contas.md)

O dicionário não depende de outros apps. O RF-55 (sinal usado em questão não pode ser excluído nem inativado) fica para a spec dos questionários, quando o modelo `Questao` existir.

## Configurações

| Configuração | Valor |
|---|---|
| `INSTALLED_APPS` | Adicionar `"django.contrib.postgres"` e `"dicionario"` |

## Normalização de termos

`TextoNormalizado.de(texto)` (`dicionario/normalizacao.py`) decompõe o texto (NFKD), remove os acentos, converte para minúsculas com `casefold()`, junta espaços repetidos e tira os espaços das pontas. Exemplo: `"  Mãe  (Família) "` → `"mae (familia)"`. A forma normalizada é usada na unicidade (RF015 ¹) e na busca (RF010 ¹).

## Modelo `Categoria`

| Campo | Tipo | Regras |
|---|---|---|
| `nome` | `CharField(60)` | Obrigatório |
| `nome_normalizado` | `CharField(60, unique=True, editable=False)` | Preenchido pelo service |
| `ativa` | `BooleanField(default=True)` | Situação Ativa ou Inativa |

Ordenação: `nome`.

## Modelo `Sinal`

| Campo | Tipo | Regras |
|---|---|---|
| `termo` | `CharField(100)` | Obrigatório. Termos com mais de um sinal levam o sentido entre parênteses, como "manga (fruta)" |
| `termo_normalizado` | `CharField(100, unique=True, editable=False)` | Preenchido pelo service |
| `classe_gramatical` | `CharField(20, choices=ClasseGramatical, blank=True)` | `SUBSTANTIVO`, `VERBO`, `ADJETIVO`, `ADVERBIO`, `OUTROS` |
| `categoria` | `ForeignKey(Categoria, PROTECT, null=True, blank=True, related_name="sinais")` | `PROTECT` impede excluir categoria com sinais (RF-53) |
| `descricao_execucao` | `CharField(500, blank=True)` | |
| `video` | `FileField(upload_to=caminho_video_sinal, validators=[VideoMp4Validator()])` | Obrigatório |
| `ativo` | `BooleanField(default=True)` | Situação Ativo ou Inativo |

- `caminho_video_sinal` gera `sinais/<uuid4>.mp4`, sem usar o nome enviado (RS012).
- Índice `sinal_termo_trgm`: `GinIndex` com `gin_trgm_ops` em `termo_normalizado`. Ele acelera a busca por parte do termo (`LIKE '%texto%'`), que um índice B-tree comum não atende. A migração cria a extensão `pg_trgm` (`TrigramExtension`) antes do índice. A extensão é confiável (*trusted*) desde o PostgreSQL 13, então o dono do banco consegue criá-la sem ser superusuário.
- A unicidade de `termo_normalizado` também gera um índice B-tree.
- Ordenação: `termo`. A colação pt-BR do banco já ordena sem diferenciar maiúsculas e acentos.

## Validador de vídeo (`dicionario/validadores.py`)

`VideoMp4Validator(tamanho_maximo=50 MB)` recusa arquivos acima do limite e arquivos cujo conteúdo não começa com a caixa `ftyp` do MP4 (bytes 4 a 8), mesmo que a extensão seja `.mp4`. A mensagem é "Arquivo inválido: envie um vídeo MP4 de até 50 MB". O limite de 50 MB é o do RF015 no documento de requisitos de 23/11/2026.

## Exceções (`dicionario/exceptions.py`)

`ErroDeDicionario` é a base de `TermoJaCadastrado`, `CategoriaJaCadastrada` e `CategoriaComSinaisAtivos`.

## Services

### `CadastroComNomeUnicoService` (base)

Classe base dos dois cadastros, que têm um campo de texto único sem diferenciar maiúsculas e acentos. As subclasses definem `modelo`, `campo`, `campo_normalizado` e `excecao_duplicado`.

| Método | Regra |
|---|---|
| `validar_unico(valor, ignorar_pk=None)` | Levanta `excecao_duplicado` se outro registro tiver a mesma forma normalizada |
| `salvar(objeto)` | Preenche o campo normalizado, chama `validar_regras(objeto)` e `validar_unico` e grava. Se o banco recusar por `IntegrityError` (gravação simultânea), levanta `excecao_duplicado` |
| `validar_regras(objeto)` | Gancho para as subclasses. Na base, não faz nada |

### `CategoriaService(CadastroComNomeUnicoService)`

| Método | Regra |
|---|---|
| `validar_inativacao(categoria_id, ativa)` | Levanta `CategoriaComSinaisAtivos` ao inativar uma categoria já gravada que tem sinais ativos (RF-53) |
| `validar_regras(categoria)` | Chama `validar_inativacao` |
| `opcoes_ativas()` | Lista de `(id, nome)` das categorias ativas, em ordem de nome, para o filtro da busca (RF-41) |

### `SinalService(CadastroComNomeUnicoService)`

Sem regras extras nesta spec. O RF-55 será acrescentado em `validar_regras` pela spec dos questionários.

### `DicionarioService` (busca do aluno)

| Método | Regra |
|---|---|
| `filtrar(queryset, texto="", categoria_id=None)` | Com texto, filtra `termo_normalizado__contains` pela forma normalizada do texto. Com categoria, filtra também pela categoria, desde que ela esteja ativa. Também é usado pela pesquisa do Admin |
| `buscar(texto="", categoria_id=None, pagina=1) -> Page` | Somente sinais ativos, com `filtrar`. Ordena por `termo`, com 20 por página. Página inexistente vira a última (`Paginator.get_page`). Usa `select_related("categoria")` |

`tem_criterio(texto, categoria_id) -> bool` diz se há o que buscar. A busca é obrigatória quando não há categoria (RF010 ¹, documento de 23/11/2026): sem texto e sem categoria, a view não chama `buscar` e a tela só mostra a orientação "Digite uma palavra ou escolha uma categoria para ver os sinais."

## Form `BuscaSinalForm` (GET)

| Campo | Regras | Mensagem |
|---|---|---|
| `busca` | Opcional, de 2 a 100 caracteres depois de tirar os espaços | "Digite ao menos 2 caracteres" |
| `categoria` | `ChoiceField` opcional, com "Todas" (valor vazio) e as opções vindas de `CategoriaService.opcoes_ativas()`, que a view passa ao form | |

## Rotas (`app_name = "dicionario"`)

`core/urls.py` inclui `dicionario.urls` em `dicionario/`.

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/dicionario/` | `dicionario:busca` | `BuscaView` | GET | Autenticado (`LoginRequiredMixin`) |

## Comportamento

### `BuscaView`

- O visitante é redirecionado para o login com `next` (RF-39).
- Com o form válido e um critério (`DicionarioService.tem_criterio`), chama `DicionarioService.buscar` e mostra os resultados. Sem critério, mostra só a orientação. Com o form inválido, mostra a mensagem junto ao campo e nenhum resultado.
- Sem resultados, exibe "Nenhum sinal encontrado. Revise o termo ou escolha outra categoria" (RF-42).
- Cada sinal mostra o termo, o vídeo (`<video controls loop muted playsinline preload="metadata">`, que o aluno pode pausar) e, quando houver, a classe gramatical, a categoria e a descrição da execução (RF-43).
- A paginação mantém os filtros nos links.
- O menu do layout base ganha o link "Dicionário" para usuários autenticados (RF-39).

## Admin

### `CategoriaAdmin`

- `list_display`: nome e situação. `list_filter`: `ativa`. `search_fields`: nome. `list_per_page = 20`.
- O form do Admin chama `CategoriaService.validar_unico` em `clean_nome` e `validar_inativacao` em `clean_ativa`, para que a mensagem apareça no campo: "Categoria já cadastrada" ou "Existem sinais ativos nesta categoria". `save_model` chama `CategoriaService.salvar`.
- A exclusão de uma categoria com sinais é barrada pelo `PROTECT`, e o Admin mostra os sinais que impedem a exclusão.

### `SinalAdmin`

- `list_display`: termo, categoria, classe gramatical e situação. `list_filter`: categoria e `ativo`. `search_fields`: termo. `get_search_results` usa a forma normalizada, para que "mae" encontre "Mãe". `list_select_related = ("categoria",)`, `list_per_page = 20`, ordem alfabética (RF-59).
- O form do Admin chama `SinalService.validar_unico` em `clean_termo` ("Termo já cadastrado"), e `save_model` chama `SinalService.salvar`.
- O detalhe mostra uma prévia do vídeo, somente leitura.
- As inclusões, alterações e exclusões ficam no `LogEntry` do Admin (RF-60).

## Limites aceitos nesta versão

- O RF-55 depende das questões e entra na spec 0004.
- Os vídeos antigos não são apagados do disco ao trocar ou excluir um sinal.
- A validação de MP4 confere a assinatura do arquivo, e não se o vídeo é reproduzível.

## Testes

- [x] `TextoNormalizado` remove acentos, maiúsculas e espaços repetidos.
- [x] `CategoriaService.salvar` recusa nome repetido com acento ou maiúscula diferente.
- [x] `CategoriaService.salvar` recusa inativar categoria com sinal ativo e aceita inativar categoria só com sinais inativos.
- [x] `SinalService.salvar` preenche `termo_normalizado` e recusa termo repetido ("Mãe" e "mae").
- [x] Editar um sinal sem mudar o termo não acusa duplicidade.
- [x] `VideoMp4Validator` aceita MP4 válido e recusa arquivo com outra assinatura ou acima do limite.
- [x] `buscar` encontra "Mãe" com "mae" e com parte do termo, ignora sinais inativos, filtra por categoria ativa e ordena por termo.
- [x] `buscar` pagina com 20 sinais e trata página inexistente.
- [x] `opcoes_ativas` não lista categorias inativas.
- [x] A migração cria o índice GIN com `gin_trgm_ops` em `termo_normalizado`.
- [x] Visitante em `/dicionario/` é redirecionado para o login.
- [x] Aluno vê os resultados, a mensagem de nenhum resultado e a mensagem de busca com 1 caractere.
- [x] Sem busca e sem categoria, nenhum sinal é listado.
- [x] O menu mostra "Dicionário" só para usuários autenticados.
- [x] O Admin recusa termo repetido com mensagem no campo e cria o sinal com o nome de arquivo gerado.
- [x] O Admin recusa inativar categoria com sinais ativos e não exclui categoria com sinais.
- [x] A pesquisa do Admin encontra sinal sem acento.
