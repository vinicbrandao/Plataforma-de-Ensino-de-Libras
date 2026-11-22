# ADR 0005: E-mails exibidos no console em desenvolvimento

- **Status:** Proposto
- **Data:** 2026-11-21

## Contexto

Funcionalidades da versão 1 e do bônus enviam e-mails: o link de recuperação de senha (RF004), o aviso ao responsável legal (RF002) e, no futuro, os lembretes (RF011). Enviar e-mails de verdade exige um servidor SMTP ou um serviço externo, com credenciais e configuração de domínio, o que a equipe não tem em desenvolvimento.

## Decisão

Em desenvolvimento, o projeto usa o backend `django.core.mail.backends.console.EmailBackend`, configurado em `MAILERS` no `settings.py`. Os e-mails aparecem no terminal do `runserver`, e nada é enviado.

O código envia e-mails pelas APIs do Django (`send_mail` e semelhantes), sem depender do backend. Nos testes, o Django troca o backend pelo de memória (`django.core.mail.outbox`).

## Consequências

- Os fluxos com e-mail podem ser testados sem conta externa, copiando o link do terminal.
- Nenhum e-mail chega a uma caixa real, então não se verifica formatação em clientes de e-mail nem entrega.
- Antes de uma implantação real, será preciso configurar um backend SMTP com credenciais vindas do ambiente e registrar isso em um novo ADR.
