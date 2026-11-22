# Spec 0005: Conteúdo inicial para a demonstração

- **Status:** Implementado
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md)
- **Depende de:** [Spec 0002](0002-dicionario.md), [Spec 0003](0003-trilha.md), [Spec 0004](0004-questionarios.md)

O comando `python manage.py criar_conteudo_inicial` cadastra conteúdo suficiente para demonstrar os RFs da versão 1 no navegador. Não muda o que o produto faz, então não há RF novo no PRD.

## Onde fica

- Comando: `questionarios/management/commands/criar_conteudo_inicial.py`. O app `questionarios` é o único que já depende de `trilha` e de `dicionario` (veja `arquitetura.md`).
- Regra: `ConteudoInicialService` (`questionarios/services/conteudo_inicial.py`). O comando só lê as opções, chama o service e imprime o relatório.
- Dados: `questionarios/conteudo_inicial.py`, com as categorias, os sinais, os módulos, as aulas e as questões.

## Conteúdo

| Item | Quantidade | Observação |
|---|---|---|
| Categorias | 3 | Saudações, Família e Cores |
| Sinais | 15 | 5 por categoria, sem descrição da execução (a equipe completa pelo Admin) |
| Módulos | 3 | Primeiros passos; Família e pessoas; Cores e cotidiano |
| Aulas | 6 | 2 por módulo |
| Questões | 18 | 3 por aula, com 3 alternativas e uma correta. Conceituais, sem descrever a execução de sinais |

## Arquivos (`amostras/`)

A pasta padrão é `BASE_DIR / "amostras"`, e a opção `--pasta` aponta outra. Os nomes esperados estão em `amostras/LEIA-ME.md`:

- `aulas/m<módulo>-a<aula>.mp4` e `aulas/m<módulo>-a<aula>.vtt` (por exemplo, `m1-a1.mp4`);
- `sinais/<termo-sem-acento>.mp4` (por exemplo, `mae.mp4`, `bom-dia.mp4`).

Cada arquivo passa pelos validadores do campo (`VideoMp4Validator`, `LegendaVttValidator`) antes de ser usado. Um arquivo que não passa conta como faltando, com o motivo. O conteúdo de `amostras/` fica fora do Git, exceto o `LEIA-ME.md`.

## `ConteudoInicialService.criar(pasta) -> RelatorioConteudo`

Tudo é gravado pelos services, com as mesmas regras do Admin. O comando pode rodar várias vezes sem duplicar:

| Item | Como é encontrado | Se não existir |
|---|---|---|
| Categoria | Nome normalizado | `CategoriaService.salvar` |
| Sinal | Termo normalizado | Com o vídeo, `SinalService.salvar`. Sem vídeo, não é criado (o vídeo é obrigatório) e entra em "faltando" |
| Módulo | Título, sem diferenciar maiúsculas | `ModuloService.salvar` na posição prevista ou, se ela estiver ocupada por outro módulo, na próxima livre |
| Aula | Módulo e título | `AulaService.salvar` sem publicar, com o vídeo e a legenda que existirem |
| Questões | A aula já tem questões | 3 questões pelo `QuestaoService`, com as alternativas validadas por `validar_alternativas` |

- Em uma aula existente, os arquivos que faltavam e agora existem são anexados.
- A aula é publicada por `AulaService.salvar` quando tem vídeo, legenda e questões, e só se ainda não estiver publicada. Sem vídeo ou legenda, fica não publicada.
- Cada item é gravado em sua própria transação: uma falha não desfaz o que já foi criado.

`RelatorioConteudo` informa o que foi criado, o que já existia, as aulas publicadas e não publicadas e a lista de arquivos faltando ou inválidos.

## Saída do comando

Um resumo por tipo (criados e já existentes), as aulas não publicadas e, em destaque, os arquivos que faltam, com o caminho esperado. O comando não falha por falta de arquivos.

## Testes

- [x] Com todos os arquivos, cria 3 categorias, 15 sinais, 3 módulos, 6 aulas publicadas e 18 questões.
- [x] Rodar duas vezes não duplica nada.
- [x] Sem arquivos, cria categorias, módulos, aulas não publicadas e questões, não cria sinais e lista os 27 arquivos faltando.
- [x] Acrescentar os arquivos e rodar de novo anexa os vídeos e as legendas e publica as aulas.
- [x] Um arquivo com assinatura inválida conta como faltando.
- [x] Um módulo da equipe na posição 1 não impede a criação: o módulo do conteúdo vai para a próxima posição livre.
- [x] O comando imprime os arquivos que faltam.
