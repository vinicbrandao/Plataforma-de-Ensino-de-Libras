# ADR 0008: Prática com câmera adiada para depois da versão 1

- **Status:** Aceito
- **Data:** 2026-11-24
- **Substitui:** [ADR 0007](0007-plataforma-sem-pratica-com-camera.md)

## Contexto

O [ADR 0007](0007-plataforma-sem-pratica-com-camera.md) retirou do produto a prática de sinais com câmera (RF008). O documento de requisitos de 23/11/2026 manteve o RF008, com prioridade Desejável e a nota "Previsto para versão posterior; a versão 1 não inclui a prática com câmera". Os outros requisitos passaram a funcionar com e sem a câmera:

- RF007: a aula é concluída com a aprovação no questionário; quando o RF008 existir, a prática também passa a ser exigida, em qualquer ordem.
- RF013: os sinais da prática só são exigidos para publicar quando o RF008 estiver implementado.
- RF015: o gabarito do sinal é opcional e só é exigido para usar o sinal na prática.

Portanto, a câmera não saiu do produto: só não entra na versão 1.

## Decisão

1. A versão 1 não tem prática com câmera. O RF008, o gabarito do sinal (RF015), os sinais da prática da aula (RF013), as tentativas de prática no histórico (RF012) e os requisitos ligados à câmera (RNF005, RNF006, RNF008 e RS005) ficam para uma versão posterior, sem tabelas nem telas nesta versão.
2. A aula é concluída pela aprovação no questionário (RF007), como já faz o `QuestionarioService`.
3. Quando o RF008 for implementado, a conclusão passa a exigir também a prática. O `ProgressoService.concluir` continua sendo o único ponto que conclui uma aula, para que essa mudança fique em um só lugar.

## Consequências

- O código atual não muda: a conclusão pelo questionário e a publicação sem sinais da prática já seguem esta decisão.
- O documento de requisitos e a documentação do projeto voltam a concordar: o RF008 existe, mas está fora da versão 1.
- Custo: a implementação futura do RF008 exige migração (gabarito do sinal, sinais da aula, tentativas de prática) e a revisão da conclusão da aula, que hoje depende só do questionário.
