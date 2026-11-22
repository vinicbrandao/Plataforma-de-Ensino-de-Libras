# Arquitetura

O projeto segue MVT, com as regras de negócio concentradas em uma camada de services ([ADR 0001](adr/0001-mvt-com-camada-de-services.md)). O banco é PostgreSQL ([ADR 0002](adr/0002-postgresql-como-banco-de-dados.md)), e a área administrativa é o Django Admin ([ADR 0003](adr/0003-django-admin-como-area-administrativa.md)).

## Apps

O pacote `core` guarda apenas a configuração (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`). Cada domínio é um app:

| App | Responsabilidade | Requisitos |
|---|---|---|
| `contas` | Usuário customizado (`AUTH_USER_MODEL`), cadastro, login, logout, bloqueio por tentativas e Admin de usuários | RF001, RF003, RF016 (bônus: RF002, RF004, RF005) |
| `trilha` | Módulos, aulas, materiais complementares, progresso do aluno e tela da vídeo-aula | RF006, RF007, RF013 |
| `questionarios` | Questões, alternativas, tentativas e correção | RF009, RF014 |
| `dicionario` | Categorias, sinais e busca | RF010, RF015 |

Os models listados no diagrama são uma previsão. Os campos e as regras definitivos ficam nas specs.

```mermaid
flowchart LR
    subgraph contas
        Usuario
    end

    subgraph dicionario
        Categoria --> Sinal
    end

    subgraph trilha
        Modulo --> Aula
        Aula --> MaterialComplementar
        ProgressoAula
    end

    subgraph questionarios
        Questao --> Alternativa
        Tentativa
    end

    ProgressoAula -->|aluno| Usuario
    ProgressoAula -->|aula| Aula
    Questao -->|aula| Aula
    Questao -.->|sinal opcional| Sinal
    Tentativa -->|aluno| Usuario
    Tentativa -->|aula| Aula
    questionarios ==>|"aprovação conclui a aula (ADR 0004)"| trilha
```

### Dependências entre apps

- `dicionario` não depende de nenhum outro app.
- `trilha` depende de `contas` (o aluno do progresso).
- `questionarios` depende de `trilha` (a aula) e de `dicionario` (o sinal da questão). Na aprovação, chama o service de progresso da `trilha` para concluir a aula ([ADR 0004](adr/0004-conclusao-da-aula-pelo-questionario.md)).
- `trilha` não importa `questionarios`. Para exigir ao menos uma questão antes de publicar (RF013), o service da trilha consulta a relação reversa da aula (`aula.questoes`), sem importar classes do outro app. Assim os imports não formam ciclo.
- Todo model que aponta para o usuário usa `settings.AUTH_USER_MODEL`.

## Camadas

```mermaid
flowchart LR
    Requisicao([Requisição]) --> URL
    URL --> View
    View -->|valida a entrada| Form
    View -->|chama| Service
    Admin[Django Admin] -->|valida e grava por| Service
    Service -->|levanta| Excecao[Exceção de domínio]
    Service --> Model[Model / ORM]
    Model --> BD[(PostgreSQL)]
    Excecao -.->|a view converte em resposta| View
    View -->|renderiza| Template
    View -->|redireciona| Redirect
    Template --> Resposta([Resposta])
    Redirect --> Resposta
```

### Organização de cada app

```text
<app>/
├── models/         um módulo por model, reexportados em __init__.py
├── services/       uma classe de service por domínio
├── views/          um módulo por tela
├── forms/
├── templates/<app>/
├── tests/
├── exceptions.py   exceções de domínio do app
├── admin.py
└── urls.py         com app_name
```

### Views (`<app>/views/`)

- Toda view é uma classe que herda diretamente de `django.views.View` e implementa apenas os métodos HTTP necessários (`get`, `post`).
- Mixins de controle de acesso, como `LoginRequiredMixin`, são permitidos. Views baseadas em função e generic views (`ListView`, `CreateView` etc.) não são usadas.
- A view só lê a entrada, chama o service e devolve a resposta (template ou redirect). Não contém regra de negócio nem acessa o ORM, e por isso não usa `get_object_or_404`.
- A view converte exceções de domínio em respostas HTTP, como `Http404` ou uma mensagem no formulário.
- `login()` e `logout()` são chamados na view, pois alteram a sessão HTTP e precisam de `request`. A verificação das credenciais e do bloqueio fica no service.

### Forms (`<app>/forms/`)

- Validam o formato da entrada (tamanho, máscara, CPF, datas) e renderizam os campos.
- Regras que dependem do estado do sistema, como e-mail já cadastrado, ficam no service.
- A gravação é feita pelo service, sem `form.save()`.

### Services (`<app>/services/`)

- São classes, como `CadastroService` ou `ProgressoService`, que agrupam as operações de um domínio.
- Toda regra de negócio fica aqui, incluindo as validações de negócio e as consultas ao ORM.
- Recebem dados simples ou objetos de domínio. Não recebem `request` nem retornam `HttpResponse`.
- Comunicam falhas com exceções de domínio (`<app>/exceptions.py`).
- Usam `transaction.atomic()` quando uma operação faz mais de uma escrita dependente.

### Models (`<app>/models/`)

- Definem campos, relacionamentos, constraints, índices, `Meta` e `__str__`, sem regra de negócio.
- As invariantes de dados ficam também no banco, com `UniqueConstraint` e `CheckConstraint` ([ADR 0002](adr/0002-postgresql-como-banco-de-dados.md)).

### Templates

- Cuidam apenas da apresentação. O layout base fica em `templates/base.html`, e os templates de cada app, em `<app>/templates/<app>/`.

### Admin (`<app>/admin.py`)

- Somente usuários com `is_staff` acessam o Admin. Não existe cadastro público de administrador ([ADR 0003](adr/0003-django-admin-como-area-administrativa.md)).
- O Admin não ignora as regras dos services: `save_model`, `delete_model`, as ações e as validações que dependem de regra chamam os services.

### Arquivos enviados

- Vídeos, legendas, materiais e vídeos de sinais ficam em `MEDIA_ROOT`, com nomes gerados pelo sistema. O tipo real e o tamanho são validados antes de gravar (RS012).
- Em desenvolvimento, o Django serve `MEDIA_URL` quando `DEBUG` está ativo.

### E-mails

- São enviados pelas APIs do Django. Em desenvolvimento, aparecem no terminal ([ADR 0005](adr/0005-emails-no-console-em-desenvolvimento.md)).

## Exemplos

Leitura:

```python
class TrilhaView(View):
    def get(self, request):
        trilha = TrilhaService.montar(aluno=request.user if request.user.is_authenticated else None)
        return render(request, "trilha/trilha.html", {"trilha": trilha})
```

Alteração, com a exceção de domínio convertida em resposta HTTP:

```python
class QuestionarioView(LoginRequiredMixin, View):
    def post(self, request, aula_id):
        form = RespostasForm(request.POST)
        if not form.is_valid():
            return render(request, "questionarios/questionario.html", {"form": form})
        try:
            tentativa = QuestionarioService.corrigir(
                aula_id=aula_id, aluno=request.user, respostas=form.cleaned_data["respostas"]
            )
        except AulaNaoEncontrada as exc:
            raise Http404 from exc
        return redirect("questionarios:resultado", tentativa_id=tentativa.id)
```
