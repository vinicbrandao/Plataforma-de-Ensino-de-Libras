# ADR 0010: Papel dono do banco chamado libras_owner

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O [ADR 0006](0006-estruturas-do-banco-em-sql.md) define três papéis no PostgreSQL: o dono das tabelas, que roda as migrações, `libras_app` e `libras_relatorio`. O dono se chamava `plataforma_libras`, o mesmo nome do banco, o que confunde o papel com o banco na entrega de Laboratório de Banco de Dados e nos scripts. A equipe planejou os papéis como `libras_owner`, `libras_app` e `libras_relatorio`.

## Decisão

1. O papel dono do banco e das tabelas passa a se chamar `libras_owner`. O banco continua `plataforma_libras`.
2. No banco existente, a troca é feita pelo `postgres` com `ALTER ROLE plataforma_libras RENAME TO libras_owner`, que mantém a senha SCRAM, a posse dos objetos e os privilégios padrão já concedidos.
3. O README, o `.env.example`, o valor padrão em `core/settings.py`, `docs/banco/contas.sql` e `docs/banco/verificacao.sql` usam o novo nome. As outras regras do ADR 0006 continuam valendo.

## Consequências

- Os três papéis seguem o mesmo padrão de nome, e o DDL entregue mostra `libras_owner` como dono.
- Custo: cada máquina com o banco já criado precisa renomear o papel uma vez, como `postgres`, e trocar `POSTGRES_USER` no `.env`.
- O ADR 0006 cita o nome antigo; este ADR registra a troca.
