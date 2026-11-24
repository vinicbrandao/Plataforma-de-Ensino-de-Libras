# Spec 0006: Histórico de desempenho

- **Status:** Implementado
- **Requisitos:** RF-62 a RF-68 do [PRD 0001](../prd/0001-plataforma-libras-v1.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0008](../adr/0008-pratica-com-camera-adiada.md)
- **Depende de:** [Spec 0004](0004-questionarios.md)

> **Revisão de 24/11/2026:** o escopo da versão 1 deixa o RF012 de fora, mas esta spec já estava implementada, e a equipe decidiu mantê-la como extra. As duas mensagens passaram a ser as do documento de requisitos de 23/11.

O aluno consulta as tentativas dos questionários que a spec 0004 já registra na tabela `Tentativa`. Não há model nem migration novos: a tela só lê.

## Onde fica

No app `questionarios`, dono de `Tentativa`. O app já depende de `trilha`, então pode ler `Aula` e `Modulo` sem criar ciclo.

## Exceção (`questionarios/exceptions.py`)

| Exceção | Mensagem |
|---|---|
| `PeriodoInvalido(ErroDeQuestionario)` | "A data final não pode ser anterior à data inicial" |

## `HistoricoService` (`questionarios/services/historico.py`)

Toda consulta começa por `Tentativa.objects.filter(aluno=aluno)`. Assim, o aluno nunca recebe tentativas de outra pessoa, seja qual for o filtro enviado (RF-68, RS004).

| Método | Regra |
|---|---|
| `opcoes(aluno) -> OpcoesHistorico` | Módulos e aulas que aparecem nas tentativas do aluno, inclusive os de aulas despublicadas (RF-66). Os módulos vêm em ordem de posição. As aulas vêm agrupadas pelo título do módulo, em ordem de posição. Os filtros só oferecem o que o aluno respondeu, sem expor títulos de aulas não publicadas que ele nunca viu |
| `consultar(aluno, filtros: FiltrosHistorico, pagina) -> Historico` | Levanta `PeriodoInvalido` se `data_final < data_inicial` (RF-64). Aplica os filtros preenchidos, combinados com E: `aula__modulo_id`, `aula_id`, `aprovada` e a data local de `realizada_em` (`realizada_em__date__gte` e `__lte`, no fuso `America/Sao_Paulo`). Ordena por `-realizada_em`, `-id` e pagina com 20 por página (RF-63), com `select_related("aula__modulo")`. Página fora do intervalo cai na última, como no `Paginator.get_page` |

Dataclasses imutáveis:

- `FiltrosHistorico`: `modulo_id: int | None`, `aula_id: int | None`, `aprovada: bool | None`, `data_inicial: date | None`, `data_final: date | None`. Tudo `None` por padrão.
- `OpcoesHistorico`: `modulos: list[tuple[int, str]]` e `aulas: list[tuple[str, list[tuple[int, str]]]]`, no formato de choices agrupadas do Django.
- `ResumoAula`: `modulo: str`, `aula: str`, `tentativas: int`, `primeira_aprovacao: datetime | None`.
- `Historico`: `pagina: Page` e `resumo: tuple[ResumoAula, ...]`. A propriedade `vazio` indica que o aluno não tem nenhuma tentativa, com ou sem filtro: o resumo tem uma linha por aula respondida.

O resumo por aula (RF-65) usa todas as tentativas do aluno, sem os filtros, porque informa o total de tentativas de cada aula. É uma única consulta agregada: `values("aula")` com `Count("id")` e `Min("realizada_em", filter=Q(aprovada=True))`, em ordem de posição do módulo e da aula.

## Form `FiltroHistoricoForm` (`questionarios/forms/historico.py`)

Formulário GET, sem gravação. As opções vêm do service, pela view, como no dicionário.

| Campo | Tipo | Regras |
|---|---|---|
| `modulo` | `TypedChoiceField(coerce=int, empty_value=None)` | Opcional, "Todos" como padrão |
| `aula` | `TypedChoiceField(coerce=int, empty_value=None)` | Opcional, "Todas" como padrão, com as aulas agrupadas por módulo |
| `resultado` | `TypedChoiceField` com "Todos", "Aprovado" e "Reprovado" | Opcional. Converte para `True`, `False` ou `None` |
| `data_inicial` e `data_final` | `DateField` com `type="date"` | Opcionais. Aceitam `AAAA-MM-DD`, que o navegador envia, e `DD/MM/AAAA` |

`filtros()` devolve um `FiltrosHistorico` com os valores limpos. Um id que não está nas opções é recusado pela validação de escolha do próprio Django.

## Rotas (`app_name = "questionarios"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/historico/` | `questionarios:historico` | `HistoricoView` | GET | Usuário autenticado. O visitante vai ao login (RF-62) |

## Comportamento

### `HistoricoView(LoginRequiredMixin, View)`

- **GET:** monta o form com `request.GET` e as opções de `HistoricoService.opcoes(request.user)`. Com o form válido, chama `consultar` com a página de `?pagina=`.
  - `PeriodoInvalido` vira o erro no campo `data_final`, e os filtros preenchidos continuam na tela (RNF-01).
  - Com o form inválido, a tela mostra os erros e o resumo, sem a lista.
- **Tela:**
  - Sem nenhuma tentativa, mostra só "Nenhuma tentativa registrada até o momento" (RF-67), sem filtros nem resumo.
  - Com tentativas, mostra os filtros, a tabela de tentativas (data e hora `dd/mm/aaaa hh:mm`, módulo, aula, "X de Y" com o percentual e o resultado) e a paginação, que mantém os filtros nos links.
  - Com filtros que não encontram nada, mostra "Nenhum registro encontrado para os filtros informados".
  - O resumo por aula fica abaixo, com módulo, aula, total de tentativas e a data da primeira aprovação, ou "Ainda não aprovado".
  - O resultado é escrito por extenso ("Aprovado" ou "Reprovado"), e não indicado só por cor (RNF-02).
- A tabela usa `<caption>`, `<th scope="col">` e rolagem horizontal própria abaixo de 360 px (RNF-03).
- O menu ganha o link "Histórico" para usuários autenticados que não são administradores. Um administrador que abrir a rota vê a mensagem de histórico vazio, pois as tentativas dele não são gravadas (spec 0004).

## Limites aceitos nesta versão

- A tentativa guarda só os números, e não as respostas. O histórico não mostra o detalhe por questão.
- O filtro de aula não depende do módulo escolhido. Os dois combinam com E, e uma combinação incoerente só não encontra tentativas.
- As tentativas continuam visíveis no Admin, somente para leitura (spec 0004).

## Testes

- [x] O visitante é levado ao login.
- [x] O aluno vê só as próprias tentativas, mesmo filtrando por uma aula de outro aluno, que é recusada como escolha inválida.
- [x] As tentativas aparecem da mais recente para a mais antiga, 20 por página, e a segunda página traz o restante.
- [x] Cada filtro funciona sozinho e combinado: módulo, aula, resultado, data inicial e data final, inclusive no limite do dia.
- [x] Data final anterior à inicial é recusada pelo service e mostrada no campo.
- [x] O resumo mostra o total de tentativas e a data da primeira aprovação de cada aula, ou "Ainda não aprovado", e ignora os filtros.
- [x] Tentativas de aula despublicada continuam no histórico e nas opções de filtro.
- [x] Sem tentativas, aparece "Nenhuma tentativa registrada até o momento". Com filtros sem resultado, aparece a mensagem de filtro.
- [x] A listagem faz um número fixo de consultas, sem N+1.
- [x] O menu mostra "Histórico" ao aluno e não ao visitante nem ao administrador.
