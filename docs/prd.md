# PRD — Plataforma de Ensino de Libras

O documento de requisitos de produto (PRD) completo da versão 1 está em [prd/0001-plataforma-libras-v1.md](prd/0001-plataforma-libras-v1.md). Este arquivo é a porta de entrada para ele: o PRD fica numa pasta numerada para que versões futuras ganhem um arquivo próprio, sem reescrever o atual.

## Resumo da versão 1

- **Objetivo:** ensinar Libras por uma trilha de módulos com vídeo-aulas legendadas, questionários e um dicionário de sinais, com a área administrativa no Django Admin.
- **Perfis:** visitante, aluno, responsável legal (só recebe e-mails) e administrador.
- **Núcleo:** RF001 (cadastro), RF003 (login), RF006 (trilha e progresso), RF007 (vídeo-aula), RF009 (questionário), RF010 (dicionário) e RF013 (gestão de módulos e aulas).
- **Pelo Django Admin:** RF014 (questionários), RF015 (dicionário) e RF016 (usuários).
- **Bônus implementados:** RF017 (sinais favoritos), RF019 (anotações), RF018 (avaliação da aula), RF020 (fale conosco), RF004 (recuperação de senha), RF005 (perfil) e RF002 (cadastro de menor, simplificado).
- **Extra:** RF012 (histórico dos questionários).
- **Fora da versão 1:** RF008 (prática com câmera, adiada pelo [ADR 0008](adr/0008-pratica-com-camera-adiada.md)) e RF011 (lembretes por e-mail).

O PRD descreve esses requisitos como RF-01 a RF-110, verificáveis, e liga cada um à sua spec em [specs/](specs/). A fonte dos IDs é o [documento de requisitos](requisitos.md).
