# ADR 0007: A plataforma não tem prática de sinais com câmera

- **Status:** Substituído por [ADR 0008](0008-pratica-com-camera-adiada.md)
- **Data:** 2026-11-22

## Contexto

O documento de requisitos previa a prática de sinais com a câmera do aluno (RF008): o navegador reconheceria os gestos e os compararia com um gabarito de cada sinal, capturado na área administrativa (RF015). A conclusão da aula exigia essa prática e a aprovação no questionário (RF007).

O RF008 ficou fora da versão 1 por ser o requisito mais complexo, e o [ADR 0004](0004-conclusao-da-aula-pelo-questionario.md) tratou a conclusão pelo questionário como provisória, até a prática existir. A equipe decidiu que a plataforma não terá essa funcionalidade: o ensino é feito por vídeos disponibilizados pela plataforma, questionários e o dicionário de sinais. Esta é uma decisão da equipe, posterior à Ata de Reunião 1.

## Decisão

- O RF008 é removido do produto, e não apenas adiado. Ele mantém o seu ID no documento de requisitos, marcado como removido, para não quebrar as referências do PRD e das specs.
- A aula é concluída com a aprovação no questionário, de forma definitiva (RF007).
- Os requisitos que dependiam da câmera perdem essa parte: os sinais da prática da aula (RF013), o gabarito do sinal (RF015), o histórico das práticas (RF012), o tempo de resposta da prática (RNF05), a regra sobre imagens da câmera (RNF06), a exigência de câmera no dispositivo (RNF08) e o requisito de segurança RS005.

## Consequências

- O código da versão 1 não muda: a câmera nunca foi implementada, e a conclusão pelo questionário já é a regra em vigor.
- A plataforma deixa de avaliar a execução dos sinais pelo aluno: a conclusão mede apenas a compreensão.
- O documento de requisitos (.docx) precisa ser atualizado pela equipe, incluindo a matriz de rastreabilidade, a matriz de risco e a contagem de pontos de função.
- O RF012 fica mais simples, porque passa a mostrar só o histórico dos questionários, que a tabela `Tentativa` já registra.
