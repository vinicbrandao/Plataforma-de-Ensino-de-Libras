# ADR 0004: Na versão 1, a aula é concluída com a aprovação no questionário

- **Status:** Proposto
- **Data:** 2026-11-21

## Contexto

Pelo RF007, a aula é concluída quando o aluno conclui a prática com câmera (RF008) e é aprovado no questionário (RF009), em qualquer ordem. O RF008 ficou fora da versão 1 ([PRD 0001](../prd/0001-plataforma-libras-v1.md)), porque depende de reconhecimento de gestos no navegador e da captura de gabaritos dos sinais.

Sem a prática, alguma regra precisa definir a conclusão, pois o status da aula e o progresso da trilha (RF006) dependem dela. As alternativas eram concluir ao assistir ao vídeo até o fim, o que exigiria acompanhar a reprodução e não mede aprendizado, ou concluir com a aprovação no questionário.

## Decisão

Na versão 1, a aula passa a Concluída quando o aluno é aprovado no questionário, com ao menos 70% de acertos (RF009). Como a publicação exige ao menos uma questão (RF013), toda aula publicada pode ser concluída.

As demais regras do RF007 continuam valendo: a data e a hora da conclusão são registradas, uma aula concluída permanece concluída e refazer o questionário não muda o status.

A regra fica em um único método de service, para que a prática com câmera possa ser incluída depois sem alterar as views.

## Consequências

- O progresso da trilha funciona sem a prática com câmera.
- A conclusão da versão 1 mede apenas a compreensão, e não a execução dos sinais.
- Quando o RF008 for implementado, este ADR será substituído, e as aulas já concluídas continuarão concluídas, mesmo sem a prática.
