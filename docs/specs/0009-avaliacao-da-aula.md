# Spec 0009: Avaliação da aula

- **Status:** Implementado
- **Requisitos:** RF-80 a RF-85 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF018 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0003](../adr/0003-django-admin-como-area-administrativa.md), [ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)
- **Depende de:** [Spec 0003](0003-trilha.md), [Spec 0008](0008-anotacoes-da-aula.md) (a exceção `AcaoSomenteDoAluno`)

O aluno dá uma nota de 1 a 5 e um comentário opcional a cada aula, e o administrador consulta as médias. Pelo ADR 0009, o model é criado antes da tela.

## Model `AvaliacaoAula` (`trilha/models/avaliacao.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `ForeignKey(AUTH_USER_MODEL, PROTECT, related_name="avaliacoes")` | |
| `aula` | `ForeignKey(Aula, PROTECT, related_name="avaliacoes")` | Avaliações de aulas despublicadas são mantidas (RF-85) |
| `nota` | `PositiveSmallIntegerField` | De 1 a 5 |
| `comentario` | `CharField(500, blank=True)` | Texto puro, sem espaços nas pontas (RS013) |
| `avaliada_em` | `DateTimeField(default=timezone.now)` | Atualizada a cada alteração (RF-81) |

Constraints:

- `avaliacao_unica_por_aula`: `UniqueConstraint(fields=["aluno", "aula"])` (RF-81).
- `avaliacao_nota_valida`: `CheckConstraint(condition=Q(nota__gte=1, nota__lte=5))`.

## Exceção (`trilha/exceptions.py`)

| Exceção | Mensagem |
|---|---|
| `AulaNaoIniciada(ErroDeTrilha)` | "Abra a aula antes de avaliá-la". Só aparece em um POST direto, porque abrir a aula já a deixa Em andamento |

## `AvaliacaoService` (`trilha/services/avaliacao.py`)

| Método | Regra |
|---|---|
| `obter(aluno, aula) -> AvaliacaoAula \| None` | A avaliação do aluno na aula |
| `avaliar(aluno, aula_id, nota, comentario) -> tuple[AvaliacaoAula, bool]` | Aplica `ExibicaoAulaService.verificar_acesso`. Recusa administrador (`AcaoSomenteDoAluno`). Exige `ProgressoAula` do aluno na aula, Em andamento ou Concluída (`AulaNaoIniciada`). Cria ou substitui a avaliação com `update_or_create`, grava `avaliada_em` e devolve se foi criada (RF-81) |
| `resumo(aula) -> ResumoAvaliacoes` | Média com uma casa decimal, quantidade e os comentários não vazios, do mais recente para o mais antigo, sem dados do aluno (RF-84) |
| `com_resumo(queryset de aulas)` | Anota `media_avaliacoes` (`Avg("avaliacoes__nota")`) e `quantidade_avaliacoes` (`Count`) para a listagem do Admin |

`ResumoAvaliacoes` é uma dataclass imutável: `media: Decimal | None`, `quantidade: int`, `comentarios: tuple[tuple[datetime, int, str], ...]` (data, nota e texto).

`AulaAberta` ganha o campo `avaliacao`, preenchido só para o aluno.

## Form `AvaliacaoForm` (`trilha/forms/avaliacao.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `nota` | `TypedChoiceField(coerce=int)` com `RadioSelect`, opções "1 de 5" a "5 de 5" | Obrigatória: "Selecione uma nota de 1 a 5" (RF-80) |
| `comentario` | `CharField(max_length=500, required=False, widget=Textarea)` | Espaços nas pontas removidos |

## Rotas (`app_name = "trilha"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/aulas/<int:aula_id>/avaliacao/` | `trilha:avaliar` | `AvaliacaoView` | POST | Aluno com a aula Em andamento ou Concluída |

## Comportamento

- **`AvaliacaoView.post`:** form válido chama `avaliar` e mostra "Obrigado pela sua avaliação!" na primeira vez ou "Avaliação atualizada" depois. Redireciona para a aula, na âncora `#avaliacao`. Form inválido reapresenta a aula com a mensagem e os dados preenchidos (RNF002).
  - `AulaNaoEncontrada` vira 404, o visitante vai ao login, `AcaoSomenteDoAluno` vira 403 e `AulaNaoIniciada` vira a mensagem no formulário.
- **Tela da aula:**
  - A área "Avalie esta aula" fica no fim da tela, com as cinco estrelas em botões de rádio, cada uma com o texto "N de 5", usáveis pelo teclado (RNF003).
  - Com avaliação gravada, os campos já vêm preenchidos.
  - O visitante e o administrador não veem a área (RF-82).
  - Ninguém vê a avaliação de outro aluno (RF-83).
- **Sugestão ao concluir:** o resultado do questionário com "Aula concluída!" ganha o link "Avalie esta aula" para `#avaliacao`, sem ser obrigatório (RF-82). O template de `questionarios` só aponta para a URL da `trilha`, sem importar o app.

## Admin

### `AvaliacoesDaAulaAdmin`

Registrado para `AvaliacoesDaAula`, um model proxy de `Aula` (`proxy = True`, sem tabela), com o título "Avaliações das aulas".

- A listagem mostra módulo, aula, situação, média (uma casa decimal, ou "—") e quantidade, 20 por página, em ordem de posição, com pesquisa por título. O queryset vem de `AvaliacaoService.com_resumo`.
- O detalhe é somente leitura e mostra o resumo e os comentários com data e nota, sem nome, e-mail ou CPF (RF-84). Sem avaliações, mostra "Esta aula ainda não possui avaliações".
- Não permite incluir, alterar nem excluir.

## Limites aceitos nesta versão

- A média é calculada a cada consulta, sem cache.
- O Admin não mostra quem avaliou, nem mesmo para a equipe (RF-84).

## Testes

- [x] O banco recusa nota fora de 1 a 5 e duas avaliações do mesmo aluno na mesma aula.
- [x] `avaliar` cria e depois substitui a avaliação, atualizando a data.
- [x] `avaliar` recusa administrador, aula restrita e aula sem progresso do aluno.
- [x] Sem nota, aparece "Selecione uma nota de 1 a 5", com o comentário mantido.
- [x] As mensagens de primeira avaliação e de atualização aparecem.
- [x] O resultado aprovado do questionário mostra o link para avaliar.
- [x] O resumo calcula a média com uma casa decimal, a quantidade e os comentários, sem dados do aluno.
- [x] O Admin lista as médias, mostra "Esta aula ainda não possui avaliações" e não permite edição.
- [x] Um comentário com `<script>` aparece escapado.
