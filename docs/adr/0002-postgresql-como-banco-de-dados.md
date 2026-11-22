# ADR 0002: PostgreSQL como banco de dados

- **Status:** Aceito
- **Data:** 2026-11-21

## Contexto

O projeto também é avaliado em Laboratório de Banco de Dados, e o documento de requisitos já prevê um servidor com PostgreSQL (RNF09). Várias regras dependem do banco para valer mesmo com acessos simultâneos: e-mail e CPF únicos (RF001), títulos e posições únicos (RF013), exatamente uma alternativa correta (RF014). Outras pedem buscas que ignoram maiúsculas, minúsculas e acentos (RF010, RF015).

O SQLite, padrão do Django, dispensa instalação, mas não oferece colação nem extensões para busca sem acentos e difere do banco de produção. MySQL seria possível, mas não é o banco previsto no documento.

## Decisão

O projeto usa PostgreSQL em todos os ambientes, inclusive em desenvolvimento e nos testes, pelo driver `psycopg` 3.

As credenciais vêm de variáveis de ambiente (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`), lidas do arquivo `.env`, que não vai para o Git. O `.env.example` documenta as variáveis.

As invariantes de dados ficam no banco sempre que possível, com `UniqueConstraint` e `CheckConstraint`, inclusive restrições por expressão, como `Lower("email")`, além da validação nos services.

## Consequências

- O comportamento em desenvolvimento é o mesmo do servidor, e os recursos do PostgreSQL, como `unaccent`, colações e restrições por expressão, ficam disponíveis.
- Cada pessoa da equipe precisa instalar o PostgreSQL e criar o usuário e o banco antes de rodar o projeto, conforme o README.
- O usuário do banco precisa da permissão `CREATEDB` para que `manage.py test` crie o banco de testes.
- Os testes ficam mais lentos que com SQLite em memória.
