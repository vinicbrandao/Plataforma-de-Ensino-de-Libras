# Mudanças no documento de requisitos: retirada da prática com câmera

Decisão da equipe em 22/11/2026, registrada no [ADR 0007](../adr/0007-plataforma-sem-pratica-com-camera.md). As mudanças abaixo já estão em `docs/requisitos.md`; esta lista serve para aplicá-las no `Requisitos_da_Plataforma_de_Ensino_de_Libras_atualizado.docx`. Os IDs não são renumerados: o RF008 fica marcado como removido.

| Seção | Onde | Mudança |
|---|---|---|
| 2.1 Abrangência | 2º parágrafo | Trocar "integra Reconhecimento de Imagem. A plataforma utilizará a câmera do dispositivo do usuário para avaliar se os gestos e sinais reproduzidos pelo aluno estão corretos." por "com vídeo-aulas legendadas e um questionário ao fim de cada aula." |
| RF001 | Objetivo | Tirar "a prática com câmera (RF008)" |
| RF003 | Objetivo | Tirar "a prática com câmera (RF008)" |
| RF007 | Objetivo | "composta por vídeo, materiais de apoio e questionário" |
| RF007 | Conteúdo da aula | Apagar a linha "Prática com câmera: um ou mais sinais a reproduzir (RF008)" |
| RF007 | Regras de negócio | "A aula é concluída quando o aluno é aprovado no questionário (RF009). O vídeo não precisa ser assistido até o fim para iniciar o questionário." |
| RF007 | Regras de negócio | "refazer o questionário não altera o status"; apagar "A prática com câmera exibe aviso de login." |
| RF007 | Mensagens | "Faça login para salvar seu progresso" |
| RF008 | Seção inteira | Substituir o conteúdo por: "Removido do produto em 22/11/2026, por decisão da equipe. A plataforma ensina por vídeos, questionários e o dicionário, sem reconhecimento de gestos pela câmera." |
| RF010 | Regras de negócio | Apagar "O cadastro de sinais é o mesmo usado como referência na prática com câmera (RF008)." |
| RF012 | Objetivo | "consulte o histórico de seus questionários" |
| RF012 | Filtros | Apagar o filtro Tipo; Resultado passa a "Aprovado ou Reprovado" |
| RF012 | Dados exibidos | "Data e hora, módulo e aula"; "Resultado: acertos e Aprovado ou Reprovado" |
| RF012 | Nota ² e mensagem | "registradas no RF009"; "Nenhum questionário respondido até o momento" |
| RF013 | Cadastro de aula | Apagar o campo "Sinais da prática" e a nota ⁵; renumerar ⁶ → ⁵ e ⁷ → ⁶ |
| RF013 | Nota de publicação | "Uma aula só pode ser publicada se tiver vídeo, legenda e ao menos uma questão (RF014)." |
| RF013 | Mensagens | "A aula precisa de vídeo, legenda e questões para ser publicada" |
| RF015 | Objetivo | "os sinais usados no dicionário (RF010) e nas questões (RF014)" |
| RF015 | Cadastro de sinal | Apagar o campo "Gabarito do sinal" e a nota ⁵; renumerar ⁶ → ⁵ e escrever "Um sinal usado em questão de aula publicada não pode ser inativado" |
| RF015 | Mensagens | Apagar "Cadastre o gabarito para usar este sinal na prática" |
| RNF01 | Descrição | "ajuda na tela de questionário" |
| RNF05 | Descrição | Apagar a frase sobre o resultado da prática em 2 segundos |
| RNF06 | Descrição | Apagar "e não grava nem armazena imagens da câmera (RF008)" |
| RNF08 | Descrição | Apagar "Para a prática com câmera (RF008), o dispositivo precisa de câmera." |
| RS005 | Linha inteira | "Removido: o perigo deixou de existir com a retirada do RF008"; solução "Não se aplica" |
| 6. Matriz de risco | Células | Tirar RS005 de Remoto (D) × Insignificante (4) e colocar em Eliminado (F) × Insignificante (4) |
| 7. Matriz de rastreabilidade | Linha e coluna RF008 | Marcar "RF008 (removido)" e apagar as relações (RF007 → RF008, RF010 → RF008, RF012 → RF008 e a linha do RF008) |
| 8. Ponto de função | Linha RF008 | "RF008 (removido)", todos os valores 0 (antes, 19 pontos). Se houver total no .docx, subtrair 19 |
| 9. Protótipo | Tela Vídeo-aula | Se o protótipo mostra a área da câmera, atualizar a imagem |
