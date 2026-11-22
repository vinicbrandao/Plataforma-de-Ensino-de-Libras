# Estado atual

Atualizado em: 2026-11-22

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- As specs [0001](specs/0001-fundacao-e-contas.md) e [0002](specs/0002-dicionario.md) estão implementadas e migradas no banco local. Só a 0001 está na `main`.
- Sem commit: a spec 0002 (app `dicionario`), `docs/contexto-academico.md`, `docs/prompts-ia.md` e a linha nova do `AGENTS.md`. Cada prompt enviado à IA é registrado em `docs/prompts-ia.md`.
- O índice do Lab. BD já existe: `sinal_termo_trgm` (GIN com `pg_trgm` em `termo_normalizado`).

## Próximos passos

1. Cadastrar alguns sinais reais (MP4) pelo Admin para a demonstração do RF010 e do RF015.
2. Antes da spec da trilha, um ADR sobre as estruturas criadas por SQL nas migrações (trigger, view, índice parcial e roles), que hoje contrariam o ADR 0001 ao levar regra para o banco.
3. Spec 0003, trilha: módulos, aulas e materiais no Admin (RF013), trilha e progresso (RF006) e vídeo-aula (RF007), com a trigger em `ProgressoAula` e a view `vw_progresso_modulo`. A rota `inicio` sai de `contas.InicioView` e passa para a trilha.
4. Spec 0004, questionários: questões no Admin (RF014), questionário e conclusão da aula (RF009, ADR 0004), com o índice único parcial da alternativa correta. Acrescentar o RF-55 em `SinalService.validar_regras`.
5. Material de Lab. BD em `docs/banco/`: DDL, trigger, índice, roles `libras_app` e `libras_relatorio` (criar as roles exige a senha do `postgres`) e view.
6. Se houver tempo, specs dos bônus: RF004, RF005 e RF002. Ao implementar o RF002, retirar o bloqueio de menores (RF-61).

## Pendências

- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- O documento de requisitos chama os não funcionais de NF003 dentro dos RFs e de RNF03 na tabela. São o mesmo requisito.
- Os termos de uso exibidos no cadastro são provisórios até a equipe ter o texto final.
- `docs/contexto-academico.md` diz que `Usuario` herda de `AbstractUser`, mas o código herda de `AbstractBaseUser` e `PermissionsMixin` (login por e-mail ou CPF). A equipe decide se ajusta o texto.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF07) e `check --deploy`.
