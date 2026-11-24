# PRD 0001: Plataforma de Ensino de Libras — versão 1

- **Status:** Aceito (revisão de 2026-11-24, pelo documento de requisitos de 23/11/2026)
- **Data:** 2026-11-21, revisado em 2026-11-24
- **Especificações:** [Spec 0001: Fundação e contas](../specs/0001-fundacao-e-contas.md), [Spec 0002: Dicionário de sinais](../specs/0002-dicionario.md), [Spec 0003: Trilha, vídeo-aula e progresso](../specs/0003-trilha.md), [Spec 0004: Questionários e conclusão da aula](../specs/0004-questionarios.md), [Spec 0005: Conteúdo inicial para a demonstração](../specs/0005-conteudo-inicial.md), [Spec 0006: Histórico de desempenho](../specs/0006-historico-de-desempenho.md), [Spec 0007: Sinais favoritos](../specs/0007-sinais-favoritos.md), [Spec 0008: Anotações da aula](../specs/0008-anotacoes-da-aula.md), [Spec 0009: Avaliação da aula](../specs/0009-avaliacao-da-aula.md), [Spec 0010: Fale conosco](../specs/0010-fale-conosco.md), [Spec 0011: Recuperação de senha](../specs/0011-recuperacao-de-senha.md), [Spec 0012: Atualização de perfil](../specs/0012-atualizacao-de-perfil.md), [Spec 0013: Cadastro de menor de idade](../specs/0013-cadastro-de-menor-de-idade.md). A seção "Specs por requisito" liga cada RF à sua spec.
- **Fonte:** [Documento de requisitos](../requisitos.md). Os IDs entre parênteses (RF001, RNF003, RS010…) são os desse documento, versão de 23/11/2026.

## Objetivo

Entregar o núcleo da plataforma: o visitante cria uma conta, entra, percorre a trilha de módulos, assiste às vídeo-aulas, responde aos questionários e consulta o dicionário de sinais. O administrador mantém todo o conteúdo e os usuários pelo Django Admin ([ADR 0003](../adr/0003-django-admin-como-area-administrativa.md)).

A versão 1 ensina por vídeos, questionários e o dicionário, sem a prática de sinais com câmera: o RF008 fica para uma versão posterior, e a aula é concluída com a aprovação no questionário ([ADR 0008](../adr/0008-pratica-com-camera-adiada.md)). Os lembretes (RF011) e o histórico (RF012) também ficam fora da versão 1; o histórico, porém, já estava implementado e fica como extra.

Se houver tempo, entram os bônus, nesta ordem: RF017 (sinais favoritos), RF019 (anotações da aula), RF018 (avaliação da aula), RF020 (fale conosco), RF004 (recuperação de senha), RF005 (atualização de perfil) e RF002 (cadastro de menor, simplificado). As tabelas de RF017 a RF020 entram no banco antes das telas ([ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)).

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Visitante | Pessoa sem conta ou não autenticada | Ver a trilha, experimentar a primeira aula e criar uma conta |
| Aluno | Pessoa cadastrada e autenticada | Estudar as aulas, responder aos questionários, acompanhar o progresso e consultar o dicionário. Com os bônus: favoritar sinais, anotar e avaliar aulas, falar com a equipe, recuperar a senha e atualizar o perfil |
| Responsável legal | Responsável pelo aluno menor de idade (bônus RF002) | Não acessa o sistema; só recebe e-mails |
| Administrador | Conta da equipe, criada na implantação, com acesso ao Django Admin | Manter módulos, aulas, questões, sinais e usuários. Com os bônus: consultar as avaliações das aulas e responder às mensagens |

## Requisitos funcionais

### Cadastro (RF001)

- **RF-01:** O visitante cria uma conta informando nome completo, e-mail, CPF, senha, confirmação de senha, data de nascimento, telefone, se possui deficiência, se teve contato com Libras e o aceite dos termos de uso e da política de privacidade.
- **RF-02:** O campo "Qual deficiência" é exigido somente quando a resposta a "Possui deficiência" for "Sim, outra", e o valor é descartado quando a resposta for outra. A opção "Prefiro não informar" está disponível (RNF006).
- **RF-03:** O cadastro é recusado, sem apagar os dados digitados, quando algum campo viola as regras do RF001. Cada caso tem a sua mensagem: nome com caracteres inválidos, e-mail fora do formato, CPF com dígitos verificadores errados, senha com menos de 8 caracteres ou sem letras e números, senhas diferentes, data de nascimento futura ou de mais de 120 anos atrás, telefone que não é de celular e termos não aceitos.
- **RF-04:** Não existem dois usuários com o mesmo CPF nem com o mesmo e-mail, sem distinguir maiúsculas de minúsculas. A verificação acontece ao salvar e exibe "CPF já cadastrado" ou "E-mail já cadastrado".
- **RF-05:** O CPF e o telefone são aceitos com ou sem pontuação e gravados nos formatos XXX.XXX.XXX-XX e (XX) 9XXXX-XXXX. O e-mail é gravado em minúsculas, e os espaços extras do nome são removidos.
- **RF-06:** A data e a hora do aceite dos termos ficam registradas.
- **RF-07:** Após o cadastro, o sistema exibe "Cadastro realizado com sucesso".
- **RF-61:** Substituído pelo RF-105, com a implementação do RF002. A idade continua sendo considerada completa na data do aniversário (RF001).

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
- **RF-19:** Cada aula mostra ao aluno o status Não iniciada, Em andamento ou Concluída, em texto, além de cor e ícone (RNF003).
- **RF-20:** O aluno vê o percentual de conclusão de cada módulo e do curso, calculado sobre as aulas publicadas e arredondado para inteiro, em barra de progresso e em texto (por exemplo, "7 de 20 aulas").
- **RF-21:** O módulo recomendado pela resposta "Teve contato com Libras" é destacado com "Comece pelo Módulo X!". A recomendação não bloqueia os outros módulos.
- **RF-22:** O botão Continuar leva à aula Em andamento aberta mais recentemente. Se não houver, leva à primeira aula não concluída do módulo recomendado.
- **RF-23:** Publicar ou despublicar uma aula recalcula os percentuais e preserva as conclusões já registradas.
- **RF-24:** O aluno vê somente o próprio progresso (RS004).

### Vídeo-aula (RF007)

- **RF-25:** A aula exibe o vídeo no player nativo do navegador, carregado pausado, com legenda em português que pode ser ativada e desativada. Exibe também o texto de apoio, quando houver.
- **RF-26:** Os controles do vídeo (reproduzir, pausar, velocidade e legendas) funcionam pelo mouse e pelo teclado (RNF003).
- **RF-27:** A legenda já começa ativada para o aluno que informou deficiência auditiva no cadastro.
- **RF-28:** A aula lista os materiais complementares, que podem ser visualizados e baixados. Acessá-los não é condição para concluir a aula.
- **RF-29:** Ao abrir pela primeira vez uma aula Não iniciada, ela passa a Em andamento, e a data e a hora de início ficam registradas.
- **RF-30:** A aula é concluída quando o aluno é aprovado no questionário. A data e a hora da conclusão ficam registradas, o sistema exibe "Aula concluída!" e indica a próxima aula da trilha ([ADR 0008](../adr/0008-pratica-com-camera-adiada.md)).
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
- **RF-40:** A busca aceita de 2 a 100 caracteres, ignora maiúsculas, minúsculas e acentos e retorna os termos que contêm o texto. Com menos de 2 caracteres, aparece "Digite ao menos 2 caracteres". A busca é obrigatória quando não há categoria: sem nenhum dos dois, nenhum sinal é listado.
- **RF-41:** O filtro de categoria lista as categorias ativas, com "Todas" como padrão, e pode ser combinado com a busca.
- **RF-42:** Somente sinais ativos aparecem, em ordem alfabética, 20 por página. Sem resultados, aparece "Nenhum sinal encontrado. Revise o termo ou escolha outra categoria".
- **RF-43:** Cada sinal mostra o termo, o vídeo curto sem áudio em loop, que pode ser pausado, e, quando cadastrados, a classe gramatical, a categoria e a descrição da execução.

### Histórico de desempenho (RF012), implementado antes da revisão de 24/11

O escopo de 24/11 deixa o RF012 fora da versão 1, mas ele já estava pronto e fica como extra. Os requisitos abaixo descrevem o que existe (spec 0006).

- **RF-62:** O aluno consulta o histórico dos próprios questionários pelo menu de qualquer tela autenticada. O visitante é levado ao login.
- **RF-63:** Cada tentativa mostra a data e a hora, o módulo, a aula, os acertos e o resultado (Aprovado ou Reprovado), da mais recente para a mais antiga, 20 por página.
- **RF-64:** Os filtros de módulo, aula, resultado e período (data inicial e data final) são opcionais e podem ser combinados. Data final anterior à inicial é recusada com "A data final não pode ser anterior à data inicial".
- **RF-65:** Para cada aula respondida, o histórico mostra a quantidade total de tentativas e a data da primeira aprovação.
- **RF-66:** As tentativas de aulas despublicadas depois continuam no histórico.
- **RF-67:** Sem nenhuma tentativa registrada, aparece "Nenhuma tentativa registrada até o momento". Com filtros que não encontram nada, aparece "Nenhum registro encontrado para os filtros informados".
- **RF-68:** Cada aluno vê somente as próprias tentativas, verificadas no servidor, e o histórico não permite alterar nem excluir tentativas (RS004).

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

- **RNF-01 (mensagens):** Toda ação recusada exibe mensagem específica junto ao campo ou à ação, sem apagar os dados preenchidos (RNF002).
- **RNF-02 (acessibilidade):** Os vídeos de aula têm legenda em português, nenhuma informação depende só de cor ou de som, as imagens têm texto alternativo e as telas podem ser usadas pelo teclado (RNF003).
- **RNF-03 (responsividade):** As telas funcionam a partir de 360 px de largura, nas duas versões mais recentes do Chrome, Firefox, Edge e Safari (RNF004).
- **RNF-04 (LGPD):** O sistema coleta apenas os dados previstos, permite não informar a deficiência e não a exibe ao administrador nem a envia por e-mail (RNF006).
- **RNF-05 (senhas):** As senhas são guardadas apenas como hash com salt e nunca aparecem em logs (RS003).
- **RNF-06 (área administrativa):** O perfil de administrador é verificado no servidor a cada requisição, e o login e o logout do administrador ficam registrados com data e hora (RS009).
- **RNF-07 (arquivos):** Os arquivos enviados são validados pelo tipo real e pelo tamanho, salvos com nomes gerados pelo sistema e nunca executados no servidor (RS012).
- **RNF-08 (desempenho):** As páginas carregam em até 3 segundos em conexão de 10 Mbps (RNF005).

## Bônus, se houver tempo

Entram nesta ordem, cada um com a sua spec. As tabelas de RF017 a RF020 são criadas antes das telas ([ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)).

### Sinais favoritos (RF017)

- **RF-69:** Cada sinal do dicionário tem um botão que alterna entre "Favoritar" e "Remover dos favoritos", em texto e ícone (RNF003). As mensagens são "Sinal adicionado aos favoritos" e "Sinal removido dos favoritos".
- **RF-70:** Cada sinal é favoritado no máximo uma vez por aluno, sem limite de favoritos, e a data de inclusão fica registrada.
- **RF-71:** O filtro "Somente favoritos" do dicionário pode ser combinado com a busca e a categoria. Com o filtro ativo e a busca vazia, lista todos os favoritos, sem exigir 2 caracteres. Sem favoritos, aparece "Você ainda não tem sinais favoritos".
- **RF-72:** A lista de favoritos segue o RF010: ordem alfabética, 20 por página e só sinais ativos. Um sinal inativado some da lista e volta se for reativado. Um sinal excluído leva os favoritos junto.
- **RF-73:** O aluno vê e altera somente os próprios favoritos (RS004).

### Anotações da aula (RF019)

- **RF-74:** Na tela da aula, o aluno escreve uma anotação de 1 a 2.000 caracteres, em texto puro, com contador de caracteres restantes, e a grava pelo botão Salvar ("Anotação salva"). Acima do limite, aparece "A anotação deve ter até 2.000 caracteres" (RS013).
- **RF-75:** Cada aluno tem no máximo uma anotação por aula, editada sempre na mesma área. A data e a hora da última alteração ficam registradas.
- **RF-76:** O aluno exclui a anotação depois de confirmar "Deseja realmente excluir esta anotação?". A exclusão é definitiva e mostra "Anotação excluída".
- **RF-77:** Somente o próprio aluno vê a anotação. Ela não aparece ao administrador (RS004).
- **RF-78:** Na aula liberada ao visitante, a área de anotações mostra "Faça login para salvar anotações".
- **RF-79:** As anotações de aulas despublicadas são mantidas e voltam a aparecer se a aula for publicada de novo.

### Avaliação da aula (RF018)

- **RF-80:** No fim da tela da aula, o aluno com a aula Em andamento ou Concluída dá uma nota de 1 a 5, em estrelas com texto equivalente ("4 de 5"), e um comentário opcional de até 500 caracteres, em texto puro, sem espaços nas pontas (RS013). Sem nota, aparece "Selecione uma nota de 1 a 5".
- **RF-81:** Cada aluno tem no máximo uma avaliação por aula. Avaliar de novo substitui a anterior e atualiza a data. As mensagens são "Obrigado pela sua avaliação!" e "Avaliação atualizada". Não há exclusão.
- **RF-82:** Ao concluir a aula, a avaliação é sugerida, sem ser obrigatória e sem interferir na conclusão. O visitante não avalia.
- **RF-83:** As avaliações não aparecem a outros alunos.
- **RF-84:** Na área administrativa, o administrador consulta, por aula, a média das notas com uma casa decimal, a quantidade de avaliações e os comentários, sem o nome, o e-mail ou o CPF do aluno (RS004). Sem avaliações, aparece "Esta aula ainda não possui avaliações".
- **RF-85:** As avaliações de aulas despublicadas são mantidas.

### Fale conosco (RF020)

- **RF-86:** O aluno envia uma mensagem com assunto (Dúvida, Problema técnico, Erro em conteúdo ou Sugestão), aula relacionada opcional entre as publicadas e texto de 10 a 1.000 caracteres, em texto puro (RS013). As mensagens são "Mensagem enviada. Acompanhe a resposta em Minhas mensagens" e "A mensagem deve ter entre 10 e 1.000 caracteres".
- **RF-87:** Cada aluno envia no máximo 5 mensagens por dia. Acima disso, aparece "Limite de 5 mensagens por dia atingido. Tente novamente amanhã".
- **RF-88:** Em "Minhas mensagens", o aluno vê somente as próprias mensagens, da mais recente para a mais antiga, com a situação e a resposta (RS004). Sem mensagens, aparece "Você ainda não enviou mensagens". O aluno não altera nem exclui uma mensagem enviada.
- **RF-89:** Na área administrativa, as mensagens aparecem 20 por página, com as mais antigas não resolvidas primeiro, e podem ser filtradas por assunto e situação. O administrador vê o nome e o e-mail do aluno, sem o CPF e sem a deficiência (RNF006).
- **RF-90:** O administrador altera somente a situação (Aberta, Em análise ou Resolvida) e a resposta, de até 1.000 caracteres. Marcar como Resolvida exige a resposta ("Informe a resposta para marcar como resolvida") e registra a data e a hora da resolução. Uma mensagem Resolvida não volta a outra situação.
- **RF-91:** O envio e cada mudança de situação ficam registrados com data e hora. A resposta aparece só na plataforma, sem e-mail. As mensagens de usuários desativados são mantidas.

### Recuperação de senha (RF004)

- **RF-92:** A tela de login tem o link "Esqueci minha senha", que pede o e-mail. A resposta é sempre "Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha", e o link só é enviado a um usuário ativo, aluno ou administrador (RS002).
- **RF-93:** O link tem um código aleatório de uso único, válido por 30 minutos, que deixa de valer após o uso, ao expirar ou quando uma nova solicitação é feita. Um link que não vale mais mostra "Link expirado ou inválido" (RS008).
- **RF-94:** São aceitas no máximo 3 solicitações por hora para o mesmo e-mail. Acima disso, aparece "Muitas solicitações. Tente novamente mais tarde".
- **RF-95:** A nova senha segue as regras do RF001, precisa ser igual à confirmação ("As senhas informadas não coincidem") e diferente da atual ("A nova senha deve ser diferente da senha atual"). Ao concluir, aparece "Senha alterada com sucesso", todas as sessões do usuário são encerradas e um e-mail avisa da alteração.
- **RF-96:** A solicitação e a redefinição ficam registradas com data e hora.

### Atualização de perfil (RF005)

- **RF-97:** O aluno consulta e altera nome, e-mail, telefone, deficiência, qual deficiência e contato com Libras, com as regras do RF001. O CPF e a data de nascimento aparecem somente para leitura. Ao salvar, aparece "Dados atualizados com sucesso".
- **RF-98:** Alterar o e-mail envia um link de confirmação ao novo endereço, válido por 24 horas ("Enviamos um link de confirmação para o novo e-mail"). Até a confirmação, o e-mail anterior continua valendo. Depois dela, o endereço anterior recebe um aviso. Um link que não vale mais mostra "Link de confirmação expirado ou inválido" (RS011).
- **RF-99:** Alterar "Teve contato com Libras" atualiza o módulo recomendado na trilha.
- **RF-100:** O aluno envia uma foto de perfil opcional, JPG ou PNG de até 2 MB, que substitui a anterior e é salva com nome gerado pelo sistema. Um arquivo fora do padrão mostra "Arquivo inválido. Envie uma imagem JPG ou PNG de até 2 MB" (RS012).
- **RF-101:** A opção "Receber lembretes de estudo por e-mail", com padrão Sim, fica gravada para os lembretes (RF011).
- **RF-102:** A troca de senha exige a senha atual ("Senha atual incorreta") e segue as regras da nova senha do RF004 (RS007).
- **RF-103:** Toda alteração do perfil fica no histórico, com campo, valor anterior, valor novo, data e hora. A troca de senha fica registrada só com a data e a hora. O histórico não é alterado nem excluído (RS007).
- **RF-104:** O aluno consulta e altera somente os próprios dados (RS004).

### Cadastro de menor de idade (RF002, simplificado)

- **RF-105:** Quem tem menos de 18 anos informa, no cadastro, o nome, o vínculo (Pai, Mãe ou Tutor ou guardião legal), o CPF, o e-mail e o telefone do responsável e confirma o termo de autorização. Esses campos só aparecem, e só são exigidos, nesse caso. Este requisito substitui o RF-61.
- **RF-106:** O CPF do responsável é validado pelos dígitos verificadores e precisa ser diferente do CPF do aluno ("O CPF do responsável deve ser diferente do CPF do aluno"). O CPF e o e-mail do responsável não são únicos, porque um responsável pode ter mais de um aluno.
- **RF-107:** O aluno e o responsável são gravados juntos, com a data e a hora do aceite do termo. O responsável recebe um e-mail com o nome do aluno e a data do cadastro, sem dados sensíveis (RS006).
- **RF-108:** Enquanto o aluno for menor, ele altera os dados do responsável no perfil. Cada alteração entra no histórico (RF-103) e gera um e-mail ao endereço anterior do responsável e, se o e-mail mudou, também ao novo.
- **RF-109:** Quando o aluno completa 18 anos, os dados do responsável passam a ser somente leitura.
- **RF-110:** O administrador vê os dados do responsável somente para leitura no detalhe do aluno (RF016).

## Specs por requisito

| Requisito | Spec |
|---|---|
| RF001, RF003, RF016 | [0001: Fundação e contas](../specs/0001-fundacao-e-contas.md) |
| RF010, RF015 | [0002: Dicionário de sinais](../specs/0002-dicionario.md) |
| RF006, RF007, RF013 | [0003: Trilha, vídeo-aula e progresso](../specs/0003-trilha.md) |
| RF009, RF014 | [0004: Questionários e conclusão da aula](../specs/0004-questionarios.md) |
| Conteúdo de demonstração | [0005: Conteúdo inicial](../specs/0005-conteudo-inicial.md) |
| RF012 (extra, já implementado) | [0006: Histórico de desempenho](../specs/0006-historico-de-desempenho.md) |
| RF017 | [0007: Sinais favoritos](../specs/0007-sinais-favoritos.md) |
| RF019 | [0008: Anotações da aula](../specs/0008-anotacoes-da-aula.md) |
| RF018 | [0009: Avaliação da aula](../specs/0009-avaliacao-da-aula.md) |
| RF020 | [0010: Fale conosco](../specs/0010-fale-conosco.md) |
| RF004 | [0011: Recuperação de senha](../specs/0011-recuperacao-de-senha.md) |
| RF005 | [0012: Atualização de perfil](../specs/0012-atualizacao-de-perfil.md) |
| RF002 | [0013: Cadastro de menor de idade](../specs/0013-cadastro-de-menor-de-idade.md) |

## Simplificações desta versão

- A duplicidade de CPF e e-mail é verificada só ao salvar, e não ao sair do campo (RF001).
- A sessão expira sem aviso prévio (RF003, RS010).
- O vídeo usa o player HTML5 nativo, sem qualidade adaptativa e sem retomar do ponto em que parou (RF007).
- O dicionário não sugere termos enquanto o aluno digita (RF010).
- A legenda da aula aceita só WebVTT (.vtt), o formato lido pelo player nativo; SRT não é aceito (RF013).
- A área administrativa usa a interface padrão do Django Admin. Comportamentos de tela do documento, como a confirmação ao clicar em Cancelar (RF013), seguem o padrão do Admin ([ADR 0003](../adr/0003-django-admin-como-area-administrativa.md)).
- No RF020, as mudanças de situação ficam registradas pelo histórico do próprio Admin, com data, hora e autor (RF-60).
- No RF002, a maioridade é calculada pela data de nascimento a cada acesso, sem a rotina diária, e não há a preferência do responsável de deixar de receber avisos, que depende dos lembretes (RF011).
- No RF005, a foto de perfil aparece só na tela do perfil, porque o documento não diz onde exibi-la.

## Fora do escopo desta versão

- RF008 Prática de sinais com câmera, com o gabarito dos sinais (RF015), os sinais da prática nas aulas (RF013) e os requisitos ligados à câmera (RNF005, RNF006, RNF008 e RS005). Fica para uma versão posterior ([ADR 0008](../adr/0008-pratica-com-camera-adiada.md)).
- RF011 Lembretes e avisos por e-mail, e a rotina diária que os dispara.
- RF012 Histórico de desempenho, como requisito da versão 1. Ele já estava implementado (RF-62 a RF-68, [spec 0006](../specs/0006-historico-de-desempenho.md)), só com os questionários, e a equipe decidiu mantê-lo como extra.
- Os bônus que não forem feitos. As tabelas de RF017 a RF020 existem mesmo assim ([ADR 0009](../adr/0009-tabelas-dos-bonus-na-versao-1.md)).
- Envio real de e-mails, HTTPS, cópia de segurança diária (RNF007) e implantação em servidor.

## Critérios de conclusão

- Cada requisito implementado, de RF-01 a RF-110, e RNF-01 a RNF-07 tem ao menos um teste automatizado ou uma verificação manual descrita na spec.
- `python manage.py check`, `python manage.py test` e `python manage.py makemigrations --check` passam.
- O fluxo completo funciona no navegador: o administrador cadastra um módulo, uma aula com vídeo, legenda e questão, publica a aula e cadastra um sinal; o aluno cria a conta, entra, abre a aula, é aprovado no questionário, vê a aula concluída e o progresso atualizado e encontra o sinal no dicionário.
- O DDL entregue em Laboratório de Banco de Dados tem as tabelas de RF017 a RF020.
