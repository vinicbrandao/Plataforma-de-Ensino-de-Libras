# Estado atual

Atualizado em: 2026-11-24

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- A revisão pelo documento de requisitos de 23/11/2026 foi aprovada: PRD revisado e ADRs 0008 (câmera adiada), 0009 (tabelas dos bônus antes das telas) e 0010 (dono `libras_owner`) aceitos. O `.docx` da raiz é o v23112026.
- Implementados: o núcleo (specs 0001 a 0004), o conteúdo inicial (0005), o RF012 como extra (0006) e os sete bônus: RF017, RF019, RF018, RF020, RF004, RF005 e RF002 simplificado (specs 0007 a 0013), verificados no navegador. São 331 testes.
- Lab. BD: o dono do banco é `libras_owner`; `contas.sql` e `verificacao.sql` rodaram em 24/11; `ddl.sql`, `ddl.txt` e `entrega-lab-bd.pdf` (com os prompts 1 a 49) têm as tabelas de todos os bônus, inclusive as de RF004, RF005 e RF002. Se o `ddl.sql` mudar, copie-o de novo para `ddl.txt` e gere o PDF outra vez.
- O registro de prompts em `docs/prompts-ia.md` foi completado em 24/11 (prompts 31 a 46, transcritos do histórico). Cada novo prompt antes da entrega deve ser registrado e o PDF gerado de novo.

## Próximos passos

1. Fazer o commit do trabalho de 22 a 24/11 (cerca de 120 arquivos fora do Git).
2. Trocar pelo Admin os 27 vídeos e legendas provisórios do banco local pelos reais, quando existirem (veja `amostras/LEIA-ME.md`). A demonstração já funciona com os provisórios: 3 módulos, 6 aulas publicadas, 18 questões e 15 sinais.
3. Corrigir no `.docx` a matriz de rastreabilidade sem RF017 a RF020, a "seção 9" de protótipos e o "(SE)" da Consulta Externa.

## Pendências

- Outras máquinas com o banco antigo precisam renomear o papel `plataforma_libras` para `libras_owner` e trocar `POSTGRES_USER` no `.env` (comando no README).
- As senhas de `libras_app` e `libras_relatorio` em `contas.sql` são placeholders (`troque_esta_senha`). Troque com `ALTER ROLE` antes de usar essas contas fora do desenvolvimento.
- `docs/relatorios/mudancas-requisitos-sem-camera.md` ficou superado: o documento de 23/11 adiou o RF008 em vez de retirá-lo.
- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- Os termos de uso exibidos no cadastro são provisórios até a equipe ter o texto final.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF007) e `check --deploy`.
