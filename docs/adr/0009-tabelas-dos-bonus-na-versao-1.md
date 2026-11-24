# ADR 0009: Tabelas dos bônus RF017 a RF020 criadas antes das telas

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

Laboratório de Banco de Dados avalia o SQL de construção do banco ([contexto acadêmico](../contexto-academico.md)). A equipe quer que esse SQL tenha as tabelas dos bônus RF017 (sinais favoritos), RF018 (avaliação da aula), RF019 (anotações da aula) e RF020 (fale conosco), mesmo as que não chegarem a ter tela na versão 1.

O [ADR 0006](0006-estruturas-do-banco-em-sql.md) faz das migrações a fonte da verdade do banco: o DDL entregue é extraído com `pg_dump` do banco criado por elas. As alternativas eram:

- **Tabelas só em um script avulso em `docs/banco/`:** atendem à entrega, mas o banco da aplicação e o dos testes ficam diferentes do entregue, contrariando o ADR 0006.
- **Models e migrações só quando cada bônus for implementado:** os bônus que não forem feitos ficam fora do DDL.
- **Models e migrações agora, telas depois:** o DDL entregue é o mesmo banco da aplicação, com todas as tabelas.

## Decisão

1. Os models dos quatro bônus são criados antes das telas, com as constraints que o documento de requisitos permite declarar, e entram nas migrações:

   | Requisito | Model | App |
   |---|---|---|
   | RF017 | `Favorito` | `dicionario` |
   | RF018 | `AvaliacaoAula` | `trilha` |
   | RF019 | `AnotacaoAula` | `trilha` |
   | RF020 | `MensagemContato` | `contato` (novo) |

2. Cada model segue a spec do seu requisito ([0007](../specs/0007-sinais-favoritos.md), [0008](../specs/0008-anotacoes-da-aula.md), [0009](../specs/0009-avaliacao-da-aula.md) e [0010](../specs/0010-fale-conosco.md)). A spec é implementada em duas partes: o model primeiro e o service, as telas e o Admin depois.
3. Enquanto o bônus não tiver tela, o model não tem service, view nem registro no Admin. Nada grava nessas tabelas.

## Consequências

- O DDL entregue tem as tabelas, as chaves e as restrições dos quatro bônus, e o banco da aplicação é o mesmo que o entregue.
- `AvaliacaoAula` e `AnotacaoAula` ficam em `trilha`, dona de `Aula`, e `Favorito` fica em `dicionario`, dono de `Sinal`. O `dicionario` passa a depender do usuário (`settings.AUTH_USER_MODEL`), como a `trilha` já depende.
- Custo: tabelas sem uso podem existir ao fim da versão 1, e implementar a tela pode exigir uma migração de ajuste se a spec mudar.
- Custo: o app `contato` existe antes de ter telas.
