# ADR 0001: MVT com camada de services e views baseadas em `View`

- **Status:** Aceito
- **Data:** 2026-11-21

## Contexto

No Django, a regra de negócio costuma se espalhar entre views, forms, models, signals e o Admin. Isso dificulta encontrar a regra, testá-la sem HTTP e reaproveitá-la. Neste projeto, o problema seria maior: o Django Admin é a área administrativa ([ADR 0003](0003-django-admin-como-area-administrativa.md)), e regras como "uma aula só é publicada com vídeo, legenda e questão" valem tanto no Admin quanto no restante do sistema.

O projeto também é avaliado em Laboratório de Programação Orientada a Objetos, que pede código organizado em classes com responsabilidades claras.

As generic views (`ListView`, `CreateView` etc.) reduzem código, mas escondem o fluxo em herança e tendem a levar regras para métodos sobrescritos.

## Decisão

O projeto segue MVT, com todas as regras de negócio e consultas ao ORM em uma camada de services que não conhece HTTP:

- Services são classes que agrupam as operações de um domínio. Elas não recebem `request` nem retornam `HttpResponse` e comunicam falhas por exceções de domínio.
- Toda view é uma classe que herda diretamente de `django.views.View`. Mixins de acesso, como `LoginRequiredMixin`, são permitidos. Views baseadas em função e generic views não são usadas.
- As ações e validações do Django Admin chamam os mesmos services.

As regras de cada camada estão em [`docs/arquitetura.md`](../arquitetura.md).

## Consequências

- As regras podem ser testadas sem cliente HTTP, e os mesmos services servem às telas do aluno e ao Admin.
- Há mais código repetitivo nas views, principalmente em formulários.
- O `ModelForm.save()` não é usado nas telas do aluno, pois a gravação é feita pelo service.
- No Admin, é preciso sobrescrever `save_model`, `delete_model` e as validações para que passem pelos services, em vez de confiar no comportamento padrão.
