# Estado atual

Atualizado em: 2026-11-22

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- As specs 0001 a 0003 estão na `main`. A [0004](specs/0004-questionarios.md) (questionários) está implementada e migrada no banco local, mas sem commit. Com ela, os 10 RFs do núcleo e do Admin da versão 1 estão implementados.
- Estruturas do Lab. BD prontas: índice `sinal_termo_trgm`, trigger `trg_progresso_conclusao`, view `vw_progresso_modulo` e índice único parcial `alternativa_correta_unica`.
- Cada prompt enviado à IA é registrado em `docs/prompts-ia.md`.

## Próximos passos

1. Material de Lab. BD em `docs/banco/`: `contas.sql` com as roles `libras_app` e `libras_relatorio` (executar exige a senha do `postgres`) e os trechos de DDL, trigger, índice e view extraídos com `sqlmigrate`.
2. Cadastrar conteúdo real pelo Admin para a demonstração: módulos, aulas com MP4 e legenda VTT, questões e sinais. Ordem na aula nova: salvar sem publicar, cadastrar as questões e só então publicar. A reprodução de um vídeo real ainda não foi testada no navegador.
3. Se houver tempo, specs dos bônus: RF004, RF005 e RF002. Ao implementar o RF002, retirar o bloqueio de menores (RF-61).

## Pendências

- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- O documento de requisitos chama os não funcionais de NF003 dentro dos RFs e de RNF03 na tabela. São o mesmo requisito.
- Os termos de uso exibidos no cadastro são provisórios até a equipe ter o texto final.
- `docs/contexto-academico.md` diz que `Usuario` herda de `AbstractUser`, mas o código herda de `AbstractBaseUser` e `PermissionsMixin` (login por e-mail ou CPF). A equipe decide se ajusta o texto.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF07) e `check --deploy`.
