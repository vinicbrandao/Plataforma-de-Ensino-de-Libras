# Estruturas que o ORM não declara: a trigger de conclusão e a view de progresso (ADR 0006).

from django.conf import settings
from django.db import migrations

CRIAR_TRIGGER = """
CREATE FUNCTION trilha_progresso_conclusao() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status = 'CONCLUIDA' THEN
        IF NEW.status <> 'CONCLUIDA' THEN
            RAISE EXCEPTION 'Uma aula concluída não pode deixar de estar concluída'
                USING ERRCODE = 'check_violation';
        END IF;
        NEW.concluida_em := OLD.concluida_em;
    ELSIF NEW.status = 'CONCLUIDA' AND NEW.concluida_em IS NULL THEN
        NEW.concluida_em := now();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_progresso_conclusao
    BEFORE INSERT OR UPDATE ON trilha_progressoaula
    FOR EACH ROW EXECUTE FUNCTION trilha_progresso_conclusao();
"""

REMOVER_TRIGGER = """
DROP TRIGGER IF EXISTS trg_progresso_conclusao ON trilha_progressoaula;
DROP FUNCTION IF EXISTS trilha_progresso_conclusao();
"""

CRIAR_VIEW = """
CREATE VIEW vw_progresso_modulo AS
SELECT
    u.id AS aluno_id,
    m.id AS modulo_id,
    COUNT(a.id)::integer AS aulas_publicadas,
    (COUNT(p.id) FILTER (WHERE p.status = 'CONCLUIDA'))::integer AS aulas_concluidas,
    ROUND(
        100.0 * COUNT(p.id) FILTER (WHERE p.status = 'CONCLUIDA') / COUNT(a.id)
    )::integer AS percentual
FROM contas_usuario AS u
CROSS JOIN trilha_modulo AS m
JOIN trilha_aula AS a
    ON a.modulo_id = m.id AND a.publicada
LEFT JOIN trilha_progressoaula AS p
    ON p.aula_id = a.id AND p.aluno_id = u.id
WHERE NOT u.is_staff
GROUP BY u.id, m.id;
"""

REMOVER_VIEW = "DROP VIEW IF EXISTS vw_progresso_modulo;"


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trilha", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(CRIAR_TRIGGER, reverse_sql=REMOVER_TRIGGER),
        migrations.RunSQL(CRIAR_VIEW, reverse_sql=REMOVER_VIEW),
    ]
