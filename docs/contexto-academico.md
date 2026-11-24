# Contexto acadêmico

Projeto em dupla do curso de Sistemas de Informação (Cesmac). A Plataforma de Ensino de Libras é o projeto da disciplina de Engenharia de Software e também é avaliada por Laboratório de Programação (POO) e por Laboratório de Banco de Dados.

## Engenharia de Software

- O documento de requisitos (Requisitos_da_Plataforma_de_Ensino_de_Libras_atualizado.docx, convertido em docs/requisitos.md) segue o template do professor e continua descrevendo o sistema completo: RFs, RNFs, requisitos de segurança, matriz de risco, matriz de rastreabilidade, pontos de função e protótipos.
- O professor fez o papel de cliente na reunião de levantamento (Ata de Reunião 1, 15/10/2026). Toda decisão de escopo deve ser rastreável até a Ata ou registrada como decisão da equipe.
- Os professores aconselharam ter pelo menos 7 requisitos funcionais realmente funcionando. O escopo da versão 1 está no PRD 0001: núcleo com RF001, RF003, RF006, RF007, RF009, RF010 e RF013, mais RF014, RF015 e RF016 pelo Django Admin, e os bônus RF017, RF019, RF018, RF020, RF004, RF005 e RF002 (simplificado). Ficam fora o RF008 (câmera, adiado pelo ADR 0008) e o RF011 (lembretes); o RF012 já estava pronto e ficou como extra (spec 0006).
- Cada RF implementado precisa ser demonstrável no navegador e rastreável: RF do documento → RF-xx do PRD → spec → código → testes.

## Entrega do código (exigência do projeto)

- O código deve ser orientado a objetos.
- A pasta docs é obrigatória, com PRD, ADRs, specs e arquitetura.md com diagrama Mermaid.
- O projeto labiv20262 (blog Django) foi dado só como sugestão de estrutura.

## Laboratório de Programação (POO): o que deixar evidente

Recomendação da equipe, não critério oficial. Como a disciplina avalia orientação a objetos, o código deve mostrar com clareza:
- Classes com responsabilidade única: services por domínio, forms, models e views.
- Encapsulamento: regras de negócio dentro dos services e dados acessados por métodos, não espalhados pelas views.
- Herança: Usuario herda de AbstractBaseUser e PermissionsMixin (login por e-mail ou CPF), views herdam de django.views.View e exceções de domínio herdam de uma exceção base de cada app.
- Polimorfismo: métodos sobrescritos (get, post, clean, save, métodos do Admin) e services com a mesma interface onde fizer sentido.
- Nomes em português claros e testes automatizados que exercitem as classes.

## Laboratório de Banco de Dados

- Banco: PostgreSQL. A avaliação considera somente o SQL de construção das estruturas:
  1. Criação das tabelas (DDL) mantendo as 4 integridades: entidade, domínio, referencial e definida pelo usuário.
  2. Uma trigger.
  3. Um campo indexado.
  4. Contas e permissões para acessar a estrutura.
  5. Uma view.
- A entrega é em PDF ou TXT. Migrations e código são aceitos só com o trecho relevante, não o arquivo inteiro.
- O professor exige que o PDF informe o modelo de IA usado e os prompts utilizados. Todo prompt enviado ao Claude Code é registrado em docs/prompts-ia.md, com a data e o modelo. O registro ficou parado entre os prompts 31 e 46 e foi completado em 24/11/2026 a partir do histórico da conversa.
- Proposta da versão 1: trigger em ProgressoAula (grava a data de conclusão e impede sair de Concluída), índice no termo do sinal, view vw_progresso_modulo, roles libras_app e libras_relatorio além do dono libras_owner (ADR 0010), e índice único parcial garantindo uma única alternativa correta por questão. O material de entrega fica em docs/banco/.
