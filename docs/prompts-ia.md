# Prompts enviados à IA

Registro exigido pelo professor de Laboratório de Banco de Dados (veja [contexto-academico.md](contexto-academico.md)). Cada prompt enviado ao Claude Code é transcrito sem alterações, com a data e o modelo, na ordem em que foi enviado.

- **Ferramenta:** Claude Code (aplicativo desktop, aba Code)
- **Modelo:** Claude Opus 5.5 (`claude-opus-5-5`), da Anthropic

## 2026-11-21

### 1. Plano da fundação do projeto

- **Modelo:** Claude Opus 5.5

```text
Faça primeiro um plano e espere minha aprovação antes de alterar qualquer arquivo.

Este repositório é a Plataforma de Ensino de Libras, projeto acadêmico de Engenharia de Software (também avaliado em Lab. de Programação POO e Lab. de Banco de Dados). O documento de requisitos completo está em Requisitos_da_Plataforma_de_Ensino_de_Libras_atualizado.docx, na raiz. Hoje implementamos só a versão 1 descrita no fim deste prompt.

Faça, nesta ordem, sem implementar funcionalidades ainda:
1. Converta o .docx para docs/requisitos.md (python-docx ou pandoc), preservando RFs, NFs, RSs e matrizes.
2. Reorganize as pastas: docs/adr, docs/prd e docs/specs lado a lado (hoje estão aninhadas em docs/adr/prd/specs). Apague index.html e style.css vazios da raiz.
3. Crie o projeto Django (pacote core) com PostgreSQL, credenciais em .env (com .env.example), .gitignore, requirements.txt, LANGUAGE_CODE pt-br, TIME_ZONE America/Sao_Paulo e um README com os passos para rodar no Windows.
4. Crie AGENTS.md e CLAUDE.md (contendo @AGENTS.md) com as regras: MVT com camada de services; regra de negócio e consultas ao ORM só nos services; views baseadas em classe herdando de django.views.View; services não recebem request nem retornam HttpResponse; código orientado a objetos; ler docs/state.md ao iniciar e atualizá-lo ao concluir; ler docs/arquitetura.md e a spec da funcionalidade antes de alterar código. Se existir .agents/skills, referencie as skills como no labiv20262.
5. Escreva docs/prd/0001-plataforma-libras-v1.md com o escopo abaixo, citando os IDs do documento.
6. Escreva os ADRs: 0001 MVT com services; 0002 PostgreSQL; 0003 Django Admin como área administrativa (RF013 a RF016, só is_staff, sem cadastro público); 0004 na v1 a aula é concluída ao ser aprovado no questionário, porque o RF008 ficou fora; 0005 e-mails no console em desenvolvimento.
7. Escreva docs/arquitetura.md com diagrama Mermaid dos apps (contas, trilha, questionarios, dicionario) e das camadas, e docs/state.md com os próximos passos.
Ao final, rode python manage.py check e diga o que falta configurar no PostgreSQL.

Escopo da versão 1:
- Núcleo: RF001 Cadastro, RF003 Login, RF006 Trilha, RF007 Vídeo-aula, RF009 Questionário, RF010 Dicionário, RF013 Gestão de módulos e aulas.
- Pelo Django Admin: RF014 Questionários, RF015 Dicionário, RF016 Usuários.
- Bônus se houver tempo: RF004, RF005 e RF002, simplificados.
- Fora: RF008 (câmera), RF011 (lembretes), RF012 (histórico).
Simplificações: duplicidade de CPF e e-mail checada só ao salvar; sem aviso antes de a sessão expirar; vídeo com player HTML5 nativo, sem qualidade adaptativa nem retomada do ponto; dicionário sem sugestão enquanto digita; publicação da aula exige vídeo, legenda e uma questão, sem exigir sinais da prática; sinais sem gabarito da câmera.
```

### 2. Aprovação do plano

- **Modelo:** Claude Opus 5.5

```text
Aprovado, pode seguir
```

## 2026-11-22

### 3. Spec 0001: fundação e contas

- **Modelo:** Claude Opus 5.5

```text
Siga o passo 3 do docs/state.md (spec de contas) e use a numeração de specs que está lá. Inclua também o Admin de usuários (RF016) nesta tarefa.

Antes de codar:
1. Marque o PRD 0001 e os ADRs 0001 a 0005 como Aceito. Respostas às questões em aberto do PRD: menor de 18 anos tem o cadastro bloqueado com mensagem até o RF002 ser implementado; a legenda aceita só VTT.
2. Me ajude a criar no PostgreSQL 18 o banco e o usuário definidos no .env.example e o arquivo .env. Eu digito a senha do usuário postgres quando você pedir.
3. Só rode migrate depois de o AUTH_USER_MODEL estar configurado.
```

### 4. Erro na criação do banco

- **Modelo:** Claude Opus 5.5

```text
Deu erro
```

### 5. Nova tentativa de criação do banco

- **Modelo:** Claude Opus 5.5

```text
Digitei, pode ler
```

### 6. Commit da spec 0001

- **Modelo:** Claude Opus 5.5

```text
Criei o superuser com meu email, nome completo e senha. Faça o commit das alterações.
```

### 7. Merge na main

- **Modelo:** Claude Opus 5.5

```text
Sim, fazer merge
```

### 8. Acesso ao banco de dados

- **Modelo:** Claude Opus 5.5

```text
Ótimo trabalho. Preciso confirmar uma coisa, por onde eu acesso o banco de dados?
```

### 9. Andamento em relação às disciplinas

- **Modelo:** Claude Opus 5.5

```text
Ok. Antes de voltarmos ao trabalho, em relação aos requisitos de avaliação das matérias de Laboratório de Banco de Dados, POO e Engenharia de Software, as presentes mudanças estão encaminhando para o cumprimento delas?
```

### 10. Contexto acadêmico

- **Modelo:** Claude Opus 5.5

```text
Salve o texto abaixo em docs/contexto-academico.md e acrescente no AGENTS.md, em "Outros documentos", uma linha mandando ler esse arquivo antes de planejar qualquer tarefa. Não altere o conteúdo.

# Contexto acadêmico

Projeto em dupla do curso de Sistemas de Informação (Cesmac). A Plataforma de Ensino de Libras é o projeto da disciplina de Engenharia de Software e também é avaliada por Laboratório de Programação (POO) e por Laboratório de Banco de Dados.

## Engenharia de Software

- O documento de requisitos (Requisitos_da_Plataforma_de_Ensino_de_Libras_atualizado.docx, convertido em docs/requisitos.md) segue o template do professor e continua descrevendo o sistema completo: RFs, RNFs, requisitos de segurança, matriz de risco, matriz de rastreabilidade, pontos de função e protótipos.
- O professor fez o papel de cliente na reunião de levantamento (Ata de Reunião 1, 15/10/2026). Toda decisão de escopo deve ser rastreável até a Ata ou registrada como decisão da equipe.
- Os professores aconselharam ter pelo menos 7 requisitos funcionais realmente funcionando. O escopo da versão 1 está no PRD 0001: núcleo com RF001, RF003, RF006, RF007, RF009, RF010 e RF013, mais RF014, RF015 e RF016 pelo Django Admin. Os RFs mais complexos (RF008, RF011 e RF012) ficam fora.
- Cada RF implementado precisa ser demonstrável no navegador e rastreável: RF do documento → RF-xx do PRD → spec → código → testes.

## Entrega do código (exigência do projeto)

- O código deve ser orientado a objetos.
- A pasta docs é obrigatória, com PRD, ADRs, specs e arquitetura.md com diagrama Mermaid.
- O projeto labiv20262 (blog Django) foi dado só como sugestão de estrutura.

## Laboratório de Programação (POO): o que deixar evidente

Recomendação da equipe, não critério oficial. Como a disciplina avalia orientação a objetos, o código deve mostrar com clareza:
- Classes com responsabilidade única: services por domínio, forms, models e views.
- Encapsulamento: regras de negócio dentro dos services e dados acessados por métodos, não espalhados pelas views.
- Herança: Usuario herda de AbstractUser, views herdam de django.views.View e exceções de domínio herdam de uma exceção base de cada app.
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
- O professor exige que o PDF informe o modelo de IA usado e os prompts utilizados. Todo prompt enviado ao Claude Code deve ser registrado em docs/prompts-ia.md, com a data e o modelo.
- Proposta da versão 1: trigger em ProgressoAula (grava a data de conclusão e impede sair de Concluída), índice no termo do sinal, view vw_progresso_modulo, roles libras_app e libras_relatorio além do dono plataforma_libras, e índice único parcial garantindo uma única alternativa correta por questão. O material de entrega fica em docs/banco/.
```

### 11. Criação deste registro

- **Modelo:** Claude Opus 5.5

```text
Sim, criar agora
```

### 12. Adiamento do commit

- **Modelo:** Claude Opus 5.5

```text
Ainda não
```

### 13. Retomada do trabalho

- **Modelo:** Claude Opus 5.5

```text
Claude, preciso saber de onde paramos.
```

### 14. Início da spec 0002 (dicionário)

- **Modelo:** Claude Opus 5.5

```text
Sim, começar
```

### 15. Aviso de commit feito

- **Modelo:** Claude Opus 5.5

```text
Já fiz o commit.
```

### 16. Início do ADR das estruturas em SQL

- **Modelo:** Claude Opus 5.5

```text
Sim, começar
```

### 17. Aceite do ADR 0006

- **Modelo:** Claude Opus 5.5

```text
Aceito
```

### 18. Commit da spec 0003 e início da spec 0004

- **Modelo:** Claude Opus 5.5

```text
Fiz o commit das mudanças. Prossiga.
```

### 19. Resumo do andamento para análise

- **Modelo:** Claude Opus 5.5

```text
Documente brevemente as alterações feitas no nosso projeto para eu enviar para analise do que ainda falta fazer.
```

### 20. Entrega de Lab. BD e conteúdo inicial

- **Modelo:** Claude Opus 5.5

```text
Execute esta tarefa do início ao fim, etapa por etapa, sem parar para pedir confirmação entre as etapas. Apresente um plano único no começo; depois de aprovado, só interrompa se um comando falhar duas vezes ou se precisar de algo que só eu posso fornecer. O que depender de mim (senha do postgres, arquivos de vídeo) fica para o relatório final, e você segue com as etapas seguintes.

Leia AGENTS.md, docs/state.md, docs/arquitetura.md, docs/contexto-academico.md, o ADR 0006 e as specs 0002 a 0004.

Etapa 1. Correções de documentação
- docs/state.md: a spec 0004 já está na main; atualize.
- docs/contexto-academico.md: troque "Usuario herda de AbstractUser" por "Usuario herda de AbstractBaseUser e PermissionsMixin (login por e-mail ou CPF)".
- Mova "Plataforma de Ensino de Libras — andamento da versão 1.pdf" da raiz para docs/relatorios/.
- Commit: "Atualiza estado do projeto e contexto acadêmico".

Etapa 2. Entrega de Lab. de Banco de Dados (DDL com as 4 integridades, trigger, campo indexado, contas e permissões, view; trigger, índices e view já existem)
- docs/banco/contas.sql, para o superusuário postgres rodar uma vez: plataforma_libras continua dona das tabelas e roda as migrations; libras_app com SELECT, INSERT, UPDATE e DELETE nas tabelas e USAGE nas sequences; libras_relatorio só com SELECT em vw_progresso_modulo; GRANTs e ALTER DEFAULT PRIVILEGES. Senhas como placeholder (troque_esta_senha), nunca reais.
- docs/banco/verificacao.sql com consultas que provam as permissões (libras_relatorio lê a view e não lê contas_usuario; libras_app não cria tabela).
- docs/banco/ddl.sql gerado com pg_dump --schema-only, usando as credenciais do .env.
- docs/banco/entrega-lab-bd.md, que vai virar o PDF: tabela das 4 integridades (entidade, domínio, referencial, definida pelo usuário) com o nome de cada constraint e o trecho SQL; a trigger trg_progresso_conclusao; os índices sinal_termo_trgm e alternativa_correta_unica; a view vw_progresso_modulo; as contas e os GRANTs; e, no fim, a ferramenta, o modelo de IA e a lista dos prompts de docs/prompts-ia.md. Só os trechos relevantes, nunca arquivos inteiros.
- Commit: "Adiciona a entrega de Lab. de Banco de Dados".

Etapa 3. Conteúdo inicial para a demonstração
- Comando python manage.py criar_conteudo_inicial, que pode rodar várias vezes sem duplicar: 3 módulos com 2 aulas publicadas cada, 3 questões por aula com alternativas e cerca de 15 sinais em 3 categorias, tudo pelos services, respeitando as regras de publicação.
- Os vídeos e legendas vêm da pasta amostras/ na raiz. Crie amostras/LEIA-ME.md com a lista exata de arquivos e nomes esperados. Se faltar arquivo quando o comando rodar, ele cria o que der sem quebrar, deixa não publicada a aula sem vídeo ou legenda e lista no terminal o que falta.
- Testes do comando sem depender dos arquivos reais. Documente no README.
- Commit: "Adiciona o comando de conteúdo inicial".

Etapa 4. Fechamento
- Rode check, test e makemigrations --check e corrija o que falhar.
- Atualize docs/state.md e registre este prompt em docs/prompts-ia.md. Commit: "Atualiza estado e registro de prompts".
- Termine com um relatório curto: o que foi feito em cada etapa, os commits criados, o comando exato para eu rodar o contas.sql como postgres e depois o verificacao.sql, e quais arquivos colocar em amostras/.
```

### 21. Aprovação do plano da entrega

- **Modelo:** Claude Opus 5.5

```text
Aprovado, execute
```

### 22. Retirada da prática com câmera

- **Modelo:** Claude Opus 5.5

```text
Claude, houve um engano, nós decidimos não fazer o uso da feature de resposta do usuário utilizando a câmera do próprio. A plataforma de libras será apenas vídeos disponibilizados pela plataforma com questionários e um dicionário. Baseado nisso, o que você mudaria no código?
```

### 23. Aprovação das mudanças de documentação

- **Modelo:** Claude Opus 5.5

```text
Sim, faça
```

### 24. Aceite do ADR 0007

- **Modelo:** Claude Opus 5.5

```text
Aceito
```

### 25. Adiamento do commit da retirada da câmera

- **Modelo:** Claude Opus 5.5

```text
Ainda não
```

### 26. Estimativa de quanto do projeto foi feito

- **Modelo:** Claude Opus 5.5

```text
Já fiz o commit. Claude, na nossa situação atual, quantos porcento do projeto você acha que foi feito?
```

### 27. Como prosseguir

- **Modelo:** Claude Opus 5.5

```text
Ótimo trabalho. Como podemos prosseguir?
```

### 28. Início da finalização da entrega de Lab. BD

- **Modelo:** Claude Opus 5.5

```text
Perfeito! Vamos começar pelo número 1.
```

### 29. PDF menor, sem o DDL completo

- **Modelo:** Claude Opus 5.5

```text
Porfavor, envie um PDF menor, tire o Anexo B e envie o ddl.sql como TXT.
Deixe que eu faço os commits a partir de agora.
```

### 30. Integridade de domínio nos campos de escolha e atualização da entrega

- **Modelo:** Claude Opus 5.5

```text
Execute do início ao fim, sem parar entre as etapas. Leia AGENTS.md, docs/state.md, o ADR 0006 e docs/banco/entrega-lab-bd.md.

1. Integridade de domínio: acrescente CheckConstraint nos models para restringir os campos de escolha aos valores permitidos, pelo menos ProgressoAula.status, Usuario.deficiencia, Usuario.contato_libras e Sinal.classe_gramatical (aceitando vazio onde o campo é opcional). Nomes no padrão <tabela>_<campo>_valido. Gere as migrations, rode migrate, check, test e makemigrations --check e corrija o que falhar.
2. Regere docs/banco/ddl.sql com pg_dump --schema-only e copie para ddl.txt.
3. Em entrega-lab-bd.md, acrescente as novas constraints na tabela de integridade de domínio. Na seção de uso de IA, acrescente: "A análise do documento de requisitos, o planejamento da versão 1 e a redação dos prompts enviados ao Claude Code foram feitos com apoio do Claude (Claude Opus 5.5), no claude.ai."
4. Registre este prompt em docs/prompts-ia.md, regenere entrega-lab-bd.pdf com os prompts atualizados e atualize docs/state.md.
5. Commit: "Reforça a integridade de domínio e atualiza a entrega de Lab. BD".
```

### 31. Encerramento do registro de prompts e retomada do trabalho

- **Modelo:** Claude Opus 5.5

```text
Perfeito. Acredito que não precisamos mais alimente o arquivo que continha os prompts para IA. Vamos continuar nosso trabalho. Por onde paramos?
```

### 32. Início do RF012 (histórico de desempenho)

- **Modelo:** Claude Opus 5.5

```text
Start RF012
```

### 33. Andamento do projeto

- **Modelo:** Claude Opus 5.5

```text
E quanto ao nosso progresso?
```

### 34. Pergunta sobre o texto do contexto acadêmico

- **Modelo:** Claude Opus 5.5

```text
Os vídeos serão adicionados amanhã. Em relação a "decidir o texto do contexto-academico.md" o que você quer dizer? Pode me fazer uma pergunta para que eu responda aqui mesmo?
```

### 35. Resposta: atualizar o contexto acadêmico

- **Modelo:** Claude Opus 5.5

```text
A
```

## 2026-11-24

### 36. Revisão pelo documento de requisitos de 23/11/2026

- **Modelo:** Claude Opus 5.5

```text
@"C:\Users\vinic\Downloads\Requisitos_da_Plataforma_de_Ensino_de_Libras_atualizadov23112026.docx"

Anexei o documento de requisitos atualizado da Plataforma de Ensino de Libras (Requisitos_da_Plataforma_de_Ensino_de_Libras_atualizadov23112026.docx). Ele é a fonte da verdade do projeto e agora tem 20 requisitos funcionais (RF001 a RF020), 9 não funcionais (RNF001 a RNF009) e 13 de segurança (RS001 a RS013).

Contexto do projeto:
- Trabalho acadêmico em dupla, que atende três disciplinas: Engenharia de Software, Laboratório de Programação (POO) e Laboratório de Banco de Dados.
- Stack: Django + PostgreSQL, arquitetura MVT com camada de services, orientação a objetos obrigatória.
- A área administrativa é o Django Admin (usuários is_staff, sem cadastro público). Em desenvolvimento, os e-mails saem no console.
- A entrega exige uma pasta docs com PRD, ADRs, specs e arquitetura.md com diagrama Mermaid.

Escopo da versão 1:
- Núcleo obrigatório: RF001, RF003, RF006, RF007, RF009, RF010 e RF013.
- Pelo Django Admin: RF014, RF015 e RF016.
- Bônus, nesta ordem, se houver tempo: RF017, RF019, RF018, RF020, RF004, RF005 e RF002 (simplificado).
- Fora da versão 1: RF008 (câmera), RF011 (lembretes) e RF012 (histórico).
- Sem o RF008, a aula é concluída com a aprovação no questionário, e os sinais da prática não são exigidos para publicar (veja RF007 e RF013).

Laboratório de Banco de Dados: o professor avalia apenas o SQL de construção. Esse SQL deve ter:
- DDL com as 4 integridades (entidade, domínio, referencial e definida pelo usuário);
- uma trigger;
- um campo indexado;
- contas e permissões;
- uma view.
O planejado é:
- uma trigger no progresso da aula, que registra a data de conclusão e impede que o status regrida de Concluída;
- um índice no termo do sinal;
- a view vw_progresso_modulo;
- os papéis libras_owner, libras_app e libras_relatorio;
- um índice único parcial que garante uma única alternativa correta por questão.
Inclua no DDL as tabelas dos RF017 a RF020, mesmo as que não forem implementadas.

O que fazer agora, sem escrever código da aplicação ainda:
1. Verifique o estado atual do repositório e diga o que já existe.
2. Converta o docx para Markdown e salve em docs/requisitos.md, preservando todos os RF, RNF, RS e matrizes.
3. Crie ou atualize docs/prd, docs/adr, docs/specs (uma spec por RF do escopo) e docs/arquitetura.md, com um diagrama Mermaid das classes e do modelo de dados. Tudo deve ser coerente com o documento de requisitos.
4. Apresente um plano de implementação em etapas pequenas, com a lista de modelos, services e telas de cada etapa e o que muda em relação ao que já existe.
5. Aponte qualquer inconsistência ou ambiguidade que encontrar nos requisitos antes de seguir.

Pare depois do plano e espere minha aprovação. Se precisar escolher algo que o documento não define, prefira a solução mais simples e registre a decisão em um ADR.
```

### 37. Aprovação do plano com as decisões recomendadas

- **Modelo:** Claude Opus 5.5

```text
Approve as recommended
```

### 38. Senha do usuário postgres (omitida neste registro)

- **Modelo:** Claude Opus 5.5

- **Observação:** a senha foi omitida deste registro.

```text
a senha do postgres é "[senha omitida]"
```

### 39. Senha digitada no terminal

- **Modelo:** Claude Opus 5.5

```text
Digitei a senha.
```

### 40. Início do RF004 (recuperação de senha)

- **Modelo:** Claude Opus 5.5

```text
Sim, seguir
```

### 41. Início do RF005 (atualização de perfil)

- **Modelo:** Claude Opus 5.5

```text
Sim, seguir
```

### 42. Início do RF002 (cadastro de menor de idade)

- **Modelo:** Claude Opus 5.5

```text
Sim, seguir
```

### 43. Relatório de progresso para a entrega

- **Modelo:** Claude Opus 5.5

```text
Claude, quero que me envie o progresso do nosso projeto até então. Preciso entrega-lo ainda hoje.
```

### 44. Plano e execução da entrega final

- **Modelo:** Claude Opus 5.5

```text
A entrega do projeto é daqui algumas horas, quais demandas precisam ser feitas para finalizarmos hoje? Quero que planeje e execute o resto dos processos. Revise os requisitos que cada matéria (Engenharia de Software, POO e Lab BD) requer e confirme sua entrega.
```

### 45. Resposta: gerar vídeos provisórios

- **Modelo:** Claude Opus 5.5

- **Observação:** resposta escolhida numa pergunta do Claude Code.

```text
Pergunta: O banco está vazio e a pasta amostras/ não tem os 27 vídeos e legendas. Como resolvemos o conteúdo para a entrega de hoje?
Resposta escolhida: Gerar vídeos provisórios
```

### 46. Resposta: completar o registro de prompts

- **Modelo:** Claude Opus 5.5

- **Observação:** resposta escolhida numa pergunta do Claude Code.

```text
Pergunta: O PDF de Lab. BD diz que todos os prompts estão transcritos, mas o registro parou no prompt 30. Como deixamos o PDF?
Resposta escolhida: Completar o registro (Recomendado)
```

### 47. Validação dos critérios de avaliação de POO (AV03)

- **Modelo:** Claude Opus 5.5

```text
@"C:\Users\vinic\Downloads\AV03.pdf"
Aqui está um pdf dos critérios de avaliação da matéria de POO. Leia o PDF e valide os critérios com o que temos pronto.
```

### 48. Criação do docs/prd.md

- **Modelo:** Claude Opus 5.5

```text
Sim, criar
```

### 49. Imagens dos protótipos removidas de propósito

- **Modelo:** Claude Opus 5.5

```text
Apaguei de propósito
```
