# Estado atual

Atualizado em: 2026-11-22

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

Nada. A [Spec 0001](specs/0001-fundacao-e-contas.md) está implementada, e o banco local já foi migrado.

## Próximos passos

1. Criar a conta de administrador com `python manage.py createsuperuser`.
2. Spec 0002, dicionário: categorias e sinais no Admin (RF015) e busca (RF010). Vem antes da trilha porque as questões referenciam sinais.
3. Spec 0003, trilha: módulos, aulas e materiais no Admin (RF013), trilha e progresso (RF006) e vídeo-aula (RF007). A rota `inicio` sai de `contas.InicioView` e passa para a trilha.
4. Spec 0004, questionários: questões no Admin (RF014), questionário e conclusão da aula (RF009, ADR 0004).
5. Se houver tempo, specs dos bônus: RF004, RF005 e RF002. Ao implementar o RF002, retirar o bloqueio de menores (RF-61).

## Pendências

- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- O documento de requisitos chama os não funcionais de NF003 dentro dos RFs e de RNF03 na tabela. São o mesmo requisito.
- Os termos de uso exibidos no cadastro são provisórios até a equipe ter o texto final.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF07) e `check --deploy`.
