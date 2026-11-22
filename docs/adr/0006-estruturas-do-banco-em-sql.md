# ADR 0006: Trigger, view e contas do banco criadas em SQL

- **Status:** Aceito
- **Data:** 2026-11-22

## Contexto

Laboratório de Banco de Dados avalia o SQL que constrói as estruturas: tabelas com as quatro integridades (entidade, domínio, referencial e definida pelo usuário), uma trigger, um campo indexado, contas com permissões e uma view ([contexto acadêmico](../contexto-academico.md)). As tabelas, constraints e índices já saem das migrações do Django, mas o ORM não declara triggers, views nem contas.

Duas dessas estruturas mexem em regras. A trigger proposta para `ProgressoAula` grava a data de conclusão e impede que uma aula concluída deixe de estar concluída, regras do RF007 e do [ADR 0004](0004-conclusao-da-aula-pelo-questionario.md). O [ADR 0001](0001-mvt-com-camada-de-services.md) põe as regras de negócio nos services, e o [ADR 0002](0002-postgresql-como-banco-de-dados.md) já admite repetir invariantes no banco, mas só por constraints.

As alternativas eram:

- **Tudo nos services, nada no banco:** cumpre o ADR 0001 à risca, mas não atende à disciplina.
- **Estruturas só em scripts avulsos em `docs/banco/`:** atendem à entrega, mas o banco da aplicação e o dos testes ficam sem elas, e os scripts se desatualizam.
- **Estruturas nas migrações:** o mesmo banco usado pela aplicação, pelos testes e pela entrega.

## Decisão

1. **Declarativo quando o Django permite.** Constraints, índices e índices únicos parciais são declarados nos models (`CheckConstraint`, `UniqueConstraint` com `condition`, `Index`, `GinIndex`). A "uma única alternativa correta por questão" (RF014) é um `UniqueConstraint(fields=["questao"], condition=Q(correta=True))`, que gera um `CREATE UNIQUE INDEX ... WHERE`.
2. **`RunSQL` para o que o ORM não declara.** A trigger e a view são criadas por `migrations.RunSQL`, sempre com `reverse_sql`, na migração do app dono da tabela. A view `vw_progresso_modulo` é lida por um model não gerenciado (`managed = False`), para que o service consulte a view pelo ORM em vez de repetir o cálculo.
3. **O service decide; o banco garante.** O service continua decidindo quando uma aula é concluída e mostrando as mensagens ao usuário. O banco é a última barreira: a trigger preenche `concluida_em` na transição para Concluída e levanta erro se alguém tentar voltar o status. O service nunca faz essa operação, então o erro só aparece se outro caminho, como SQL direto, tentar quebrar a regra.
4. **Contas fora das migrações.** Criar roles exige `CREATEROLE` ou superusuário, que o dono do banco (`plataforma_libras`) não tem. As roles ficam em `docs/banco/contas.sql`, executado uma vez pelo `postgres`:
   - `plataforma_libras`: dono das tabelas, usado pelas migrações;
   - `libras_app`: só leitura e escrita de dados (`SELECT`, `INSERT`, `UPDATE`, `DELETE` e uso das sequências), sem alterar estruturas;
   - `libras_relatorio`: só `SELECT` nas views.

   O script usa `ALTER DEFAULT PRIVILEGES`, para que as tabelas criadas por migrações futuras recebam as mesmas permissões.
5. **Material de entrega em `docs/banco/`.** Os trechos de SQL entregues são extraídos das migrações (`python manage.py sqlmigrate`) e do `contas.sql`, sem copiar arquivos inteiros. As migrações continuam sendo a fonte da verdade.

## Consequências

- O banco da aplicação, o dos testes e o da entrega têm as mesmas estruturas, e os testes cobrem a trigger e a view.
- Parte das regras do RF007 passa a existir em dois lugares, no service e na trigger. Uma mudança nessas regras exige alterar os dois, além de uma nova migração.
- O SQL da trigger e da view é específico do PostgreSQL e fica fora do que o ORM verifica. Um erro nele só aparece ao migrar ou nos testes.
- Em desenvolvimento, a aplicação continua conectando como `plataforma_libras`. Usar `libras_app` em execução exigiria duas credenciais (uma para migrar, outra para rodar), o que fica para uma eventual implantação.
- Criar as contas depende da senha do `postgres`, como na criação do banco.
