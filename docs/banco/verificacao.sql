-- Verificação das permissões criadas por contas.sql.
--
-- Executar como superusuário postgres, conectado ao banco plataforma_libras,
-- depois de contas.sql:
--   psql -U postgres -h localhost -d plataforma_libras -f docs/banco/verificacao.sql
--
-- Cada teste negativo tenta a operação com SET ROLE e mostra "OK" quando o
-- PostgreSQL a recusa por falta de privilégio (insufficient_privilege).

\echo '== 1. Privilégios por objeto (has_table_privilege) =='
SELECT conta,
       objeto,
       privilegio,
       has_table_privilege(conta, objeto, privilegio) AS permitido
FROM (VALUES ('libras_app'), ('libras_relatorio')) AS c(conta)
CROSS JOIN (VALUES
    ('contas_usuario', 'SELECT'),
    ('contas_usuario', 'INSERT'),
    ('trilha_progressoaula', 'UPDATE'),
    ('questionarios_tentativa', 'DELETE'),
    ('vw_progresso_modulo', 'SELECT')
) AS o(objeto, privilegio)
ORDER BY conta, objeto, privilegio;

\echo '== 2. Quem pode criar objetos no schema public =='
SELECT conta,
       has_schema_privilege(conta, 'public', 'USAGE') AS usa_schema,
       has_schema_privilege(conta, 'public', 'CREATE') AS cria_objetos
FROM (VALUES ('libras_owner'), ('libras_app'), ('libras_relatorio')) AS c(conta);

\echo '== 3. libras_relatorio lê a view =='
SET ROLE libras_relatorio;
SELECT count(*) AS linhas_na_view FROM vw_progresso_modulo;
RESET ROLE;

\echo '== 4. libras_relatorio NÃO lê contas_usuario =='
DO $$
BEGIN
    SET LOCAL ROLE libras_relatorio;
    PERFORM 1 FROM contas_usuario LIMIT 1;
    RAISE NOTICE 'FALHA: libras_relatorio conseguiu ler contas_usuario';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'OK: libras_relatorio não lê contas_usuario (%)', SQLERRM;
END
$$;

\echo '== 5. libras_app lê e grava dados =='
SET ROLE libras_app;
SELECT count(*) AS usuarios_visiveis FROM contas_usuario;
RESET ROLE;

\echo '== 6. libras_app NÃO cria tabela =='
DO $$
BEGIN
    SET LOCAL ROLE libras_app;
    CREATE TABLE teste_permissao (id integer);
    DROP TABLE teste_permissao;
    RAISE NOTICE 'FALHA: libras_app conseguiu criar uma tabela';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'OK: libras_app não cria tabelas (%)', SQLERRM;
END
$$;

\echo '== 7. libras_app NÃO altera a estrutura de uma tabela existente =='
DO $$
BEGIN
    SET LOCAL ROLE libras_app;
    ALTER TABLE contas_usuario ADD COLUMN teste_permissao integer;
    ALTER TABLE contas_usuario DROP COLUMN teste_permissao;
    RAISE NOTICE 'FALHA: libras_app conseguiu alterar contas_usuario';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'OK: libras_app não altera tabelas (%)', SQLERRM;
END
$$;
