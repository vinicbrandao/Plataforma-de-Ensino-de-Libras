# Spec 0007: Sinais favoritos

- **Status:** Implementado
- **Requisitos:** RF-69 a RF-73 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF017 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0006](../adr/0006-estruturas-do-banco-em-sql.md), [ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)
- **Depende de:** [Spec 0002](0002-dicionario.md)

O aluno marca sinais do dicionário como favoritos e filtra o dicionário por eles. Pelo ADR 0009, o model é criado antes da tela, na etapa das tabelas dos bônus.

## Model `Favorito` (`dicionario/models/favorito.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `ForeignKey(AUTH_USER_MODEL, PROTECT, related_name="favoritos")` | Usuários não são excluídos (RF016) |
| `sinal` | `ForeignKey(Sinal, CASCADE, related_name="favoritos")` | Excluir o sinal remove os favoritos dele (RF-72) |
| `criado_em` | `DateTimeField(default=timezone.now)` | Data de inclusão (RF-70) |

Constraint `favorito_unico_por_aluno`: `UniqueConstraint(fields=["aluno", "sinal"])` (RF-70). O índice da constraint também atende à consulta dos favoritos de um aluno. Ordenação: `sinal__termo`.

Como no resto do banco, a chave estrangeira fica `NO ACTION` no PostgreSQL, e o `CASCADE` é aplicado pelo Django (ADR 0006).

## Exceção (`dicionario/exceptions.py`)

| Exceção | Uso |
|---|---|
| `SinalNaoEncontrado(ErroDeDicionario)` | Sinal inexistente ou inativo. A view responde 404 |

## `FavoritoService` (`dicionario/services/favorito.py`)

| Método | Regra |
|---|---|
| `alternar(aluno, sinal_id) -> bool` | Só aceita sinal ativo (`SinalNaoEncontrado`). Se o favorito existe, apaga e devolve `False`. Se não existe, cria e devolve `True`. Um `IntegrityError` de dois cliques simultâneos é tratado como favorito já criado |
| `ids_dos_favoritos(aluno, sinal_ids) -> set[int]` | Quais sinais da página atual o aluno favoritou, em uma consulta, para o botão de cada sinal |
| `tem_favoritos(aluno) -> bool` | Usa `exists()`. Decide a mensagem "Você ainda não tem sinais favoritos" |

### Mudança no `DicionarioService.buscar`

Ganha `aluno` e `somente_favoritos: bool = False`. Com o filtro, aplica `favoritos__aluno=aluno` antes da busca e da categoria. As outras regras continuam: só sinais ativos, ordem alfabética, 20 por página (RF-72). Assim, um sinal inativado some da lista e volta quando é reativado, porque o favorito continua gravado.

## Form `BuscaSinalForm`

- Novo campo `favoritos`: `BooleanField(required=False, label="Somente favoritos")`.
- A busca continua exigindo 2 caracteres quando preenchida. Vazia, com o filtro ativo, é aceita (RF-71).

## Rotas (`app_name = "dicionario"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/dicionario/sinais/<int:sinal_id>/favorito/` | `dicionario:favoritar` | `FavoritoView` | POST | Aluno. Visitante vai ao login; administrador recebe 403 |

## Comportamento

### `FavoritoView(LoginRequiredMixin, View)`

- **POST:** chama `FavoritoService.alternar`. Mostra "Sinal adicionado aos favoritos" ou "Sinal removido dos favoritos" com `messages.success` e volta para a página de origem, recebida no campo `proxima` e validada com `url_has_allowed_host_and_scheme`. Sem endereço válido, volta para `dicionario:busca`.
- `SinalNaoEncontrado` vira 404. Um administrador recebe 403, pois os favoritos são do aluno (RF-73).

### Tela do dicionário

- Cada sinal ganha um formulário POST com `{% csrf_token %}` e um botão "☆ Favoritar" ou "★ Remover dos favoritos", com `aria-pressed` (RF-69, RNF003). O administrador não vê o botão.
- O formulário de busca ganha a caixa "Somente favoritos".
- Com o filtro ativo e nenhum favorito gravado, aparece "Você ainda não tem sinais favoritos". Com favoritos gravados e nenhum resultado para a busca, aparece a mensagem de sempre do dicionário.

## Admin

Sem registro. Os favoritos são dados do aluno e não têm uso administrativo (RS004).

## Limites aceitos nesta versão

- O botão recarrega a página. Não há atualização sem recarregar.
- A data de inclusão é gravada, mas não aparece na tela.

## Testes

- [x] O banco recusa o mesmo sinal favoritado duas vezes pelo mesmo aluno.
- [x] `alternar` cria e depois remove o favorito e recusa sinal inativo ou inexistente.
- [x] O filtro "Somente favoritos" lista só os favoritos do aluno, combinado com busca e categoria, e com busca vazia não exige 2 caracteres.
- [x] Sinal inativado some dos favoritos e volta ao ser reativado. Sinal excluído leva os favoritos junto.
- [x] Sem favoritos, o filtro mostra "Você ainda não tem sinais favoritos".
- [x] A rota recusa visitante (login), administrador (403) e GET (405), e não alcança favoritos de outro aluno.
- [x] O redirecionamento ignora `proxima` com outro domínio.
- [x] A página do dicionário faz um número fixo de consultas com os botões de favorito.
