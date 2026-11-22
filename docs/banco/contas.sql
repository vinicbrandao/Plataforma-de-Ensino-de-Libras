-- Contas e permissões do banco plataforma_libras (ADR 0006).
--
-- Executar UMA vez, como superusuário postgres, conectado ao banco plataforma_libras:
--   psql -U postgres -h localhost -d plataforma_libras -f docs/banco/contas.sql
-- Pode ser executado de novo sem erro: as contas só são criadas se não existirem.
--
-- Contas:
--   plataforma_libras  dona das tabelas; roda as migrations (criada no README).
--   libras_app         aplicação: lê e grava dados, sem alterar a estrutura.
--   libras_relatorio   relatórios: só lê a view vw_progresso_modulo.
--
-- As senhas abaixo são placeholders. Troque-as antes de usar as contas fora do
-- desenvolvimento, por exemplo: ALTER ROLE libras_app PASSWORD '<senha forte>';

\set ON_ERROR_STOP on

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'libras_app') THEN
        CREATE ROLE libras_app LOGIN PASSWORD 'troque_esta_senha';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'libras_relatorio') THEN
        CREATE ROLE libras_relatorio LOGIN PASSWORD 'troque_esta_senha';
    END IF;
END
$$;

-- Acesso ao banco e ao schema. Ninguém além da dona cria objetos no schema public
-- (já é o padrão do PostgreSQL 15+; o REVOKE deixa isso explícito).
GRANT CONNECT ON DATABASE plataforma_libras TO libras_app, libras_relatorio;
GRANT USAGE ON SCHEMA public TO libras_app, libras_relatorio;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- libras_app: dados das tabelas existentes (DML) e uso das sequences.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO libras_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO libras_app;

-- libras_app: as mesmas permissões nas tabelas e sequences que as próximas
-- migrations criarem como plataforma_libras.
ALTER DEFAULT PRIVILEGES FOR ROLE plataforma_libras IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO libras_app;
ALTER DEFAULT PRIVILEGES FOR ROLE plataforma_libras IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO libras_app;

-- libras_relatorio: só a view. A view executa com as permissões da dona, então
-- a conta não precisa de acesso às tabelas de origem (contas_usuario etc.).
GRANT SELECT ON vw_progresso_modulo TO libras_relatorio;

\echo 'Contas libras_app e libras_relatorio prontas.'
