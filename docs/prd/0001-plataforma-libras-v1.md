# PRD 0001: Plataforma de Ensino de Libras — versão 1

- **Status:** Aceito
- **Data:** 2026-11-21
- **Especificações:** [Spec 0001: Fundação e contas](../specs/0001-fundacao-e-contas.md), [Spec 0002: Dicionário de sinais](../specs/0002-dicionario.md), [Spec 0003: Trilha, vídeo-aula e progresso](../specs/0003-trilha.md), [Spec 0004: Questionários e conclusão da aula](../specs/0004-questionarios.md), [Spec 0005: Conteúdo inicial para a demonstração](../specs/0005-conteudo-inicial.md); a ordem das próximas está em [docs/state.md](../state.md).
- **Fonte:** [Documento de requisitos](../requisitos.md). Os IDs entre parênteses (RF001, RNF03, RS010…) são os desse documento.

## Objetivo

Entregar o núcleo da plataforma: o visitante cria uma conta, entra, percorre a trilha de módulos, assiste às vídeo-aulas, responde aos questionários e consulta o dicionário de sinais. O administrador mantém todo o conteúdo e os usuários pelo Django Admin ([ADR 0003](../adr/0003-django-admin-como-area-administrativa.md)).

A plataforma ensina por vídeos, questionários e o dicionário, sem prática de sinais com câmera: o RF008 foi removido do produto por decisão da equipe, e a aula é concluída com a aprovação no questionário ([ADR 0007](../adr/0007-plataforma-sem-pratica-com-camera.md)). Os lembretes (RF011) e o histórico (RF012) ficam para versões futuras.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Visitante | Pessoa sem conta ou não autenticada | Ver a trilha, experimentar a primeira aula e criar uma conta |
| Aluno | Pessoa cadastrada e autenticada | Estudar as aulas, responder aos questionários, acompanhar o progresso e consultar o dicionário |
| Administrador | Conta da equipe, criada na implantação, com acesso ao Django Admin | Manter módulos, aulas, questões, sinais e usuários |

## Requisitos funcionais

### Cadastro (RF001)

- **RF-01:** O visitante cria uma conta informando nome completo, e-mail, CPF, senha, confirmação de senha, data de nascimento, telefone, se possui deficiência, se teve contato com Libras e o aceite dos termos de uso e da política de privacidade.
- **RF-02:** O campo "Qual deficiência" é exigido somente quando a resposta a "Possui deficiência" for "Sim, outra", e o valor é descartado quando a resposta for outra. A opção "Prefiro não informar" está disponível (RNF06).
- **RF-03:** O cadastro é recusado, sem apagar os dados digitados, quando algum campo viola as regras do RF001. Cada caso tem a sua mensagem: nome com caracteres inválidos, e-mail fora do formato, CPF com dígitos verificadores errados, senha com menos de 8 caracteres ou sem letras e números, senhas diferentes, data de nascimento futura ou de mais de 120 anos atrás, telefone que não é de celular e termos não aceitos.
- **RF-04:** Não existem dois usuários com o mesmo CPF nem com o mesmo e-mail, sem distinguir maiúsculas de minúsculas. A verificação acontece ao salvar e exibe "CPF já cadastrado" ou "E-mail já cadastrado".
- **RF-05:** O CPF e o telefone são aceitos com ou sem pontuação e gravados nos formatos XXX.XXX.XXX-XX e (XX) 9XXXX-XXXX. O e-mail é gravado em minúsculas, e os espaços extras do nome são removidos.
- **RF-06:** A data e a hora do aceite dos termos ficam registradas.
- **RF-07:** Após o cadastro, o sistema exibe "Cadastro realizado com sucesso".
- **RF-61:** Enquanto o RF002 não for implementado, o cadastro de quem tem menos de 18 anos é recusado com a mensagem "O cadastro de menores de 18 anos ainda não está disponível". A idade é considerada completa na data do aniversário (RF001).

### Login e sessão (RF003)

- **RF-08:** O aluno entra informando e-mail ou CPF e a senha. Um valor com "@" é tratado como e-mail, sem distinguir maiúsculas de minúsculas. Os demais valores são tratados como CPF, com ou sem pontuação.
- **RF-09:** Com credenciais incorretas, o sistema exibe "Login ou senha inválidos", sem indicar qual dado está errado nem se o login existe (RS002).
- **RF-10:** Após 5 tentativas falhas seguidas para o mesmo login, as tentativas para esse login ficam bloqueadas por 15 minutos, exista ele ou não. A mensagem é "Muitas tentativas de acesso. Tente novamente em 15 minutos" (RS001).
- **RF-11:** Um usuário desativado não entra. A mensagem "Usuário desativado" só aparece quando a senha está correta.
- **RF-12:** Após o login, o aluno vai para a trilha. Se tentou abrir uma tela restrita antes de entrar, vai para essa tela.
- **RF-13:** Toda tela restrita acessada sem autenticação, inclusive digitando o endereço, redireciona para o login.
- **RF-14:** A sessão expira após 30 minutos de inatividade, sem aviso prévio (RS010).
- **RF-15:** O botão Sair aparece em todas as telas autenticadas, encerra a sessão no servidor e leva ao login. O botão Voltar do navegador não volta a exibir telas autenticadas (RS010).

### Trilha e progresso (RF006)

- **RF-16:** A trilha mostra os módulos e, dentro de cada um, as aulas publicadas, em ordem de posição. Módulos sem aulas publicadas não aparecem.
- **RF-17:** O visitante vê a trilha completa, mas só abre a primeira aula publicada do primeiro módulo. As demais exibem "Faça login para acessar esta aula" e levam ao login. O progresso do visitante não é registrado.
- **RF-18:** Para o aluno, nenhuma aula é bloqueada.
- **RF-19:** Cada aula mostra ao aluno o status Não iniciada, Em andamento ou Concluída, em texto, além de cor e ícone (RNF03).
- **RF-20:** O aluno vê o percentual de conclusão de cada módulo e do curso, calculado sobre as aulas publicadas e arredondado para inteiro, em barra de progresso e em texto (por exemplo, "7 de 20 aulas").
- **RF-21:** O módulo recomendado pela resposta "Teve contato com Libras" é destacado com "Comece pelo Módulo X!". A recomendação não bloqueia os outros módulos.
- **RF-22:** O botão Continuar leva à aula Em andamento aberta mais recentemente. Se não houver, leva à primeira aula não concluída do módulo recomendado.
- **RF-23:** Publicar ou despublicar uma aula recalcula os percentuais e preserva as conclusões já registradas.
- **RF-24:** O aluno vê somente o próprio progresso (RS004).

### Vídeo-aula (RF007)

- **RF-25:** A aula exibe o vídeo no player nativo do navegador, carregado pausado, com legenda em português que pode ser ativada e desativada. Exibe também o texto de apoio, quando houver.
- **RF-26:** Os controles do vídeo (reproduzir, pausar, velocidade e legendas) funcionam pelo mouse e pelo teclado (RNF03).
- **RF-27:** A legenda já começa ativada para o aluno que informou deficiência auditiva no cadastro.
- **RF-28:** A aula lista os materiais complementares, que podem ser visualizados e baixados. Acessá-los não é condição para concluir a aula.
- **RF-29:** Ao abrir pela primeira vez uma aula Não iniciada, ela passa a Em andamento, e a data e a hora de início ficam registradas.
- **RF-30:** A aula é concluída quando o aluno é aprovado no questionário. A data e a hora da conclusão ficam registradas, o sistema exibe "Aula concluída!" e indica a próxima aula da trilha ([ADR 0007](../adr/0007-plataforma-sem-pratica-com-camera.md)).
- **RF-31:** Uma aula concluída continua concluída, mesmo que o aluno refaça o questionário e seja reprovado.
- **RF-32:** Na aula liberada ao visitante, ele assiste ao vídeo, vê os materiais e responde ao questionário, sem nenhum registro. A aula exibe "Faça login para salvar seu progresso".
- **RF-33:** Se o vídeo não carregar, o sistema exibe "Não foi possível carregar o vídeo. Tente novamente" e um botão para tentar de novo.

### Questionário (RF009)

- **RF-34:** O questionário exibe as questões da aula na ordem definida pelo administrador. Cada questão tem um enunciado, opcionalmente o vídeo de um sinal, e de 2 a 5 alternativas.
- **RF-35:** O envio só é aceito com todas as questões respondidas. Caso contrário, aparece "Responda todas as questões antes de enviar", e as respostas já marcadas são mantidas.
- **RF-36:** O aluno é aprovado quando acerta ao menos 70% das questões.
- **RF-37:** Após o envio, o sistema mostra o número de acertos, o percentual e a alternativa correta de cada questão errada, com "Aprovado! Você acertou X de Y questões" ou "Você acertou X de Y questões. É necessário acertar 70% para concluir. Tente novamente".
- **RF-38:** O número de tentativas é ilimitado. Cada tentativa do aluno fica registrada com acertos, data e hora. Nada é registrado para o visitante.

### Dicionário (RF010)

- **RF-39:** Somente o aluno acessa o dicionário, pelo menu de qualquer tela autenticada. O visitante é levado ao login.
- **RF-40:** A busca aceita de 2 a 100 caracteres, ignora maiúsculas, minúsculas e acentos e retorna os termos que contêm o texto. Com menos de 2 caracteres, aparece "Digite ao menos 2 caracteres".
- **RF-41:** O filtro de categoria lista as categorias ativas, com "Todas" como padrão, e pode ser combinado com a busca.
- **RF-42:** Somente sinais ativos aparecem, em ordem alfabética, 20 por página. Sem resultados, aparece "Nenhum sinal encontrado. Revise o termo ou escolha outra categoria".
- **RF-43:** Cada sinal mostra o termo, o vídeo curto sem áudio em loop, que pode ser pausado, e, quando cadastrados, a classe gramatical, a categoria e a descrição da execução.

### Área administrativa (RF013 a RF016, pelo Django Admin)

- **RF-44:** Somente administradores acessam a área administrativa. Não existe cadastro público de administrador: as contas são criadas pela equipe na implantação (RS009).
- **RF-45:** O administrador cadastra módulos com título único de até 100 caracteres, descrição de até 500 e posição inteira positiva, que também é única. A comparação de títulos ignora maiúsculas, minúsculas e espaços repetidos (RF013).
- **RF-46:** O administrador cadastra aulas com módulo, título único dentro do módulo, descrição, posição única dentro do módulo, vídeo MP4, legenda em português no formato WebVTT (.vtt), texto de apoio de até 2.000 caracteres e situação, que começa como Não publicada (RF013).
- **RF-47:** Uma aula só é publicada se tiver vídeo, legenda e ao menos uma questão. Caso contrário, aparece "A aula precisa de vídeo, legenda e questões para ser publicada" (RF013).
- **RF-48:** O administrador pode abrir uma aula não publicada para vê-la como o aluno a verá (RF013).
- **RF-49:** Um módulo só é excluído se não tiver aulas. Uma aula com progresso registrado não é excluída, apenas despublicada, e despublicar preserva o progresso (RF013).
- **RF-50:** O administrador cadastra materiais complementares em uma aula, com título e arquivo PDF, JPG ou PNG de até 10 MB (RF013).
- **RF-51:** O administrador cadastra questões em uma aula, com enunciado de até 500 caracteres, sinal do dicionário opcional, posição única na aula e de 2 a 5 alternativas de até 200 caracteres, com exatamente uma correta (RF014).
- **RF-52:** A última questão de uma aula publicada não pode ser excluída. Alterar ou excluir uma questão não muda as tentativas já registradas (RF014).
- **RF-53:** O administrador cadastra categorias com nome único de até 60 caracteres e situação Ativa ou Inativa. Uma categoria com sinais ativos não é inativada, e uma categoria com sinais não é excluída (RF015).
- **RF-54:** O administrador cadastra sinais com termo único de até 100 caracteres, classe gramatical, categoria, descrição de até 500 caracteres, vídeo MP4 e situação. A unicidade de termos e nomes ignora maiúsculas, minúsculas e acentos (RF015).
- **RF-55:** Um sinal usado em questão não é excluído, e um sinal usado em questão de aula publicada não é inativado (RF015).
- **RF-56:** O administrador consulta os alunos, com nome, e-mail, data de nascimento, data de cadastro e CPF parcial (***.456.789-**), sem a informação sobre deficiência. O único campo alterável é a situação, e usuários não são excluídos (RF016).
- **RF-57:** A pesquisa de alunos aceita o CPF completo, com ou sem pontuação, parte do nome, e-mail e situação, combinados (RF016).
- **RF-58:** Ao desativar um aluno, o sistema pede confirmação e encerra imediatamente as sessões ativas dele. Ao ser reativado, o aluno mantém o progresso (RF016).
- **RF-59:** As listagens da área administrativa exibem 20 registros por página, com a ordenação e as pesquisas descritas em RF013 a RF016.
- **RF-60:** Toda inclusão, alteração e exclusão feita na área administrativa fica registrada com data, hora e autor. As consultas ao detalhe de um aluno e as mudanças de situação também ficam registradas (RS004).

## Requisitos não funcionais

- **RNF-01 (mensagens):** Toda ação recusada exibe mensagem específica junto ao campo ou à ação, sem apagar os dados preenchidos (RNF02).
- **RNF-02 (acessibilidade):** Os vídeos de aula têm legenda em português, nenhuma informação depende só de cor ou de som, as imagens têm texto alternativo e as telas podem ser usadas pelo teclado (RNF03).
- **RNF-03 (responsividade):** As telas funcionam a partir de 360 px de largura, nas duas versões mais recentes do Chrome, Firefox, Edge e Safari (RNF04).
- **RNF-04 (LGPD):** O sistema coleta apenas os dados previstos, permite não informar a deficiência e não a exibe ao administrador (RNF06).
- **RNF-05 (senhas):** As senhas são guardadas apenas como hash com salt e nunca aparecem em logs (RS003).
- **RNF-06 (área administrativa):** O perfil de administrador é verificado no servidor a cada requisição, e o login e o logout do administrador ficam registrados com data e hora (RS009).
- **RNF-07 (arquivos):** Os arquivos enviados são validados pelo tipo real e pelo tamanho, salvos com nomes gerados pelo sistema e nunca executados no servidor (RS012).
- **RNF-08 (desempenho):** As páginas carregam em até 3 segundos em conexão de 10 Mbps (RNF05).

## Bônus, se houver tempo

Entram simplificados, e cada um ganha uma spec antes de ser implementado:

- **RF004 Recuperação de senha:** link de uso único enviado ao e-mail, que em desenvolvimento aparece no terminal ([ADR 0005](../adr/0005-emails-no-console-em-desenvolvimento.md)), com mensagem igual exista o e-mail ou não (RS002).
- **RF005 Atualização de perfil:** edição dos dados alteráveis e troca de senha mediante a senha atual, sem troca de e-mail.
- **RF002 Cadastro de menor de idade:** dados do responsável e termo de autorização, com aviso por e-mail ao responsável.

## Simplificações desta versão

- A duplicidade de CPF e e-mail é verificada só ao salvar, e não ao sair do campo (RF001).
- A sessão expira sem aviso prévio (RF003, RS010).
- O vídeo usa o player HTML5 nativo, sem qualidade adaptativa e sem retomar do ponto em que parou (RF007).
- O dicionário não sugere termos enquanto o aluno digita (RF010).
- A legenda da aula aceita só WebVTT (.vtt), o formato lido pelo player nativo; SRT não é aceito (RF013).
- Menores de 18 anos não conseguem se cadastrar até o RF002 ser implementado (RF-61).
- A área administrativa usa a interface padrão do Django Admin. Comportamentos de tela do documento, como a confirmação ao clicar em Cancelar (RF013), seguem o padrão do Admin ([ADR 0003](../adr/0003-django-admin-como-area-administrativa.md)).

## Removido do produto

- RF008 Prática de sinais com câmera, com o gabarito dos sinais (RF015), os sinais da prática nas aulas (RF013) e os requisitos ligados à câmera (RNF05, RNF06, RNF08 e RS005), por decisão da equipe ([ADR 0007](../adr/0007-plataforma-sem-pratica-com-camera.md)).

## Fora do escopo desta versão

- RF011 Lembretes e avisos por e-mail, e a rotina diária que os dispara.
- RF012 Histórico de desempenho, agora restrito aos questionários: as tentativas são registradas (RF-38), mas não há tela para consultá-las.
- RF002, RF004 e RF005, se o bônus não for feito.
- Envio real de e-mails, HTTPS, cópia de segurança diária (RNF07) e implantação em servidor.

## Critérios de conclusão

- Cada requisito RF-01 a RF-61 e RNF-01 a RNF-07 tem ao menos um teste automatizado ou uma verificação manual descrita na spec.
- `python manage.py check`, `python manage.py test` e `python manage.py makemigrations --check` passam.
- O fluxo completo funciona no navegador: o administrador cadastra um módulo, uma aula com vídeo, legenda e questão, publica a aula e cadastra um sinal; o aluno cria a conta, entra, abre a aula, é aprovado no questionário, vê a aula concluída e o progresso atualizado e encontra o sinal no dicionário.
