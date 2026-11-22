# Estado atual

Atualizado em: 2026-11-22

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- As specs [0001](specs/0001-fundacao-e-contas.md) e [0002](specs/0002-dicionario.md) estão na `main`. A [0003](specs/0003-trilha.md) (trilha) está implementada e migrada no banco local, mas sem commit, junto com o ADR 0006 aceito.
- Estruturas do Lab. BD prontas: índice `sinal_termo_trgm`, trigger `trg_progresso_conclusao` e view `vw_progresso_modulo`.
- Cada prompt enviado à IA é registrado em `docs/prompts-ia.md`.

## Próximos passos

1. Spec 0004, questionários: questões no Admin (RF014), questionário e conclusão da aula (RF009), chamando `ProgressoService.concluir` (ADR 0004). Incluir o índice único parcial da alternativa correta, a exigência de uma questão em `AulaService.validar_publicacao` e o RF-55 em `SinalService.validar_regras`.
2. Material de Lab. BD em `docs/banco/`: `contas.sql` com as roles `libras_app` e `libras_relatorio` (executar exige a senha do `postgres`) e os trechos de DDL, trigger, índice e view extraídos com `sqlmigrate`.
3. Cadastrar conteúdo real pelo Admin para a demonstração: módulos, aulas com MP4 e legenda VTT, e sinais. A reprodução de um vídeo real ainda não foi testada no navegador.
4. Se houver tempo, specs dos bônus: RF004, RF005 e RF002. Ao implementar o RF002, retirar o bloqueio de menores (RF-61).

## Pendências

- Até a spec 0004, nenhuma tela conclui aulas, e a publicação ainda não exige questão.
- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- O documento de requisitos chama os não funcionais de NF003 dentro dos RFs e de RNF03 na tabela. São o mesmo requisito.
- Os termos de uso exibidos no cadastro são provisórios até a equipe ter o texto final.
- `docs/contexto-academico.md` diz que `Usuario` herda de `AbstractUser`, mas o código herda de `AbstractBaseUser` e `PermissionsMixin` (login por e-mail ou CPF). A equipe decide se ajusta o texto.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF07) e `check --deploy`.
