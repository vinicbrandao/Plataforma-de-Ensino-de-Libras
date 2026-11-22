# Regras essenciais

- O projeto segue MVT com uma camada de services, e toda regra de negócio e consulta ao ORM fica nos services.
- Toda view é uma classe que herda de `django.views.View` e implementa só os métodos HTTP necessários. Mixins de acesso, como `LoginRequiredMixin`, são permitidos.
- Services não recebem `request` nem retornam `HttpResponse`.
- O código é orientado a objetos: services são classes que agrupam as operações de um domínio, e as falhas são exceções de domínio (`<app>/exceptions.py`).

# Ao iniciar e concluir

- Ao iniciar, leia `docs/state.md`, com o trabalho em andamento, os próximos passos e as pendências.
- Ao concluir uma tarefa, atualize esse arquivo e retire o que estiver resolvido.

# Antes de alterar código

- Leia `docs/arquitetura.md`, com as regras completas de cada camada e a divisão em apps.
- Leia a especificação da funcionalidade em `docs/specs/`, seguindo a ordem da numeração. Se ela não existir, escreva-a antes do código.
- Em código Python, leia `.agents/skills/python-boas-praticas/SKILL.md`.
- Em código Django, leia também `.agents/skills/django-boas-praticas/SKILL.md`.
- Em rotas, permissões, autenticação, entrada de usuários, configurações, dependências ou revisões de segurança, leia `.agents/skills/seguranca-owasp/SKILL.md`.

# Outros documentos

- Requisitos originais (RF, RNF e RS), convertidos do .docx da raiz: `docs/requisitos.md`. Cite os IDs dele.
- Requisitos do produto: `docs/prd/`. Antes de criar ou alterar, leia `.agents/skills/prd/SKILL.md`.
- Especificações: `docs/specs/`. Antes de criar ou alterar, leia `.agents/skills/spec/SKILL.md`.
- Decisões de arquitetura: `docs/adr/`. Antes de criar ou alterar, leia `.agents/skills/adr/SKILL.md`.
