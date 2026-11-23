# Estado atual

Atualizado em: 2026-11-22

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- As specs 0001 a 0005 estão implementadas: os 10 RFs da versão 1 funcionam, e `criar_conteudo_inicial` cadastra o conteúdo de demonstração.
- A entrega de Lab. BD está pronta: `docs/banco/entrega-lab-bd.pdf` (16 páginas, com os prompts no Anexo A) e `docs/banco/ddl.txt`, cópia do `ddl.sql` enviada junto. `contas.sql` e `verificacao.sql` já foram executados no banco local, e o `ddl.sql` inclui os `GRANT`s. Se o `ddl.sql` mudar, copie-o de novo para `ddl.txt`. Os campos de escolha têm `CHECK` no banco (`<tabela>_<campo>_valido`): uma opção nova exige nova migration e um novo `ddl.sql`. O PDF registra os prompts até o 30; se forem enviados outros antes da entrega, gere o PDF de novo. O relatório de andamento enviado para análise está em `docs/relatorios/`.
- Cada prompt enviado à IA é registrado em `docs/prompts-ia.md`.
- A prática com câmera (RF008) foi removida do produto: [ADR 0007](adr/0007-plataforma-sem-pratica-com-camera.md) aceito, substituindo o ADR 0004; PRD e `requisitos.md` atualizados. O código não muda.

## Próximos passos

1. Aplicar no .docx as mudanças listadas em `docs/relatorios/mudancas-requisitos-sem-camera.md`. O `contexto-academico.md` ainda diz que o RF008 "fica fora"; a equipe decide se ajusta o texto.
2. Colocar os 27 vídeos e legendas em `amostras/` (lista em `amostras/LEIA-ME.md`) e rodar `python manage.py criar_conteudo_inicial`. Depois, completar pelo Admin a descrição da execução dos sinais e revisar o texto das questões.
3. Testar a reprodução de um vídeo real no navegador.
4. Se houver tempo, o RF012 (histórico, agora só dos questionários, com os dados da tabela `Tentativa`) e os bônus RF004, RF005 e RF002. Ao implementar o RF002, retirar o bloqueio de menores (RF-61).

## Pendências

- As senhas de `libras_app` e `libras_relatorio` em `contas.sql` são placeholders (`troque_esta_senha`). Troque com `ALTER ROLE` antes de usar essas contas fora do desenvolvimento.
- As skills citam Python 3.12, e a máquina atual usa Python 3.13. O Django 6.1 aceita os dois.
- O documento de requisitos chama os não funcionais de NF003 dentro dos RFs e de RNF03 na tabela. São o mesmo requisito.
- Os termos de uso exibidos no cadastro são provisórios até a equipe ter o texto final.
- Antes de um deploy real: `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP real (ADR 0005), backup diário (RNF07) e `check --deploy`.
