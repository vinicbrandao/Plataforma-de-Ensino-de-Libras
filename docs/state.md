# Estado atual

Atualizado em: 2026-11-21

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- Fundação pronta: projeto Django `core` configurado para PostgreSQL e `.env`, [PRD 0001](prd/0001-plataforma-libras-v1.md) e ADRs 0001 a 0005, todos com status Proposto. Nenhum app foi criado.

## Próximos passos

1. Revisar e aceitar o PRD 0001 e os ADRs 0001 a 0005, e responder às questões em aberto do PRD (menores de idade sem o RF002; legenda SRT ou só VTT).
2. Configurar o PostgreSQL local e o `.env`, conforme o README. **Não rodar `migrate` antes do passo 3.**
3. Spec 0001, fundação e contas: app `contas` com o usuário customizado (`AUTH_USER_MODEL = "contas.Usuario"`), layout base, cadastro (RF001), login e sessão (RF003, RS001, RS002, RS010) e Admin de usuários (RF016). O usuário customizado precisa existir antes da primeira migração.
4. Spec 0002, dicionário: categorias e sinais no Admin (RF015) e busca (RF010). Vem antes da trilha porque as questões referenciam sinais.
5. Spec 0003, trilha: módulos, aulas e materiais no Admin (RF013), trilha e progresso (RF006) e vídeo-aula (RF007).
6. Spec 0004, questionários: questões no Admin (RF014), questionário e conclusão da aula (RF009, ADR 0004).
7. Se houver tempo, specs dos bônus: RF004, RF005 e RF002.

## Pendências

- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- O documento de requisitos chama os não funcionais de NF003 dentro dos RFs e de RNF03 na tabela. São o mesmo requisito.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF07) e `check --deploy`.
