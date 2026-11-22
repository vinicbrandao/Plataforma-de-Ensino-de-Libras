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
