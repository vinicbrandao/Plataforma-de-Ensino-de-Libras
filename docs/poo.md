# Programação Orientada a Objetos no projeto

Guia para a avaliação de Laboratório de Programação (POO). Ele mostra onde cada pilar aparece no código, com o arquivo e a linha, para conferir durante a apresentação. A linguagem é Python 3.13, com Django 6.1 e PostgreSQL 18 pelo Django ORM.

## Os quatro pilares

| Pilar | Onde aparece | Arquivo |
|---|---|---|
| **Abstração** | `ArquivoValidator` é uma classe abstrata (`ABC`) com o método abstrato `conteudo_valido`: não pode ser instanciada, e cada subclasse diz como reconhece o seu tipo de arquivo | [core/validadores.py:16](../core/validadores.py#L16) |
| | `ParticipacaoNaAulaMixin` é abstrato: define o `post` comum e exige que cada view implemente `executar` | [trilha/views/participacao.py:21](../trilha/views/participacao.py#L21) |
| **Encapsulamento** | Toda regra de negócio e toda consulta ao banco ficam em classes de service; as views só leem a entrada e devolvem a resposta | [docs/arquitetura.md](arquitetura.md) |
| | Objetos de valor: `Cpf` valida os dígitos verificadores e expõe só `formatado` e `parcial` (propriedades); `Telefone` e `TextoNormalizado` seguem o mesmo padrão | [contas/documentos.py:12](../contas/documentos.py#L12), [dicionario/normalizacao.py:7](../dicionario/normalizacao.py#L7) |
| | Métodos internos com `_` (por exemplo `_ler_cabecalho`, `_verificar_duplicidade`, `_tokens_abertos`) e resultados em dataclasses imutáveis (`frozen=True`), como `Resultado` e `Correcao` | [questionarios/services/questionario.py:12](../questionarios/services/questionario.py#L12) |
| **Herança** | `Usuario` herda de `AbstractBaseUser` e `PermissionsMixin` (login por e-mail ou CPF) | [contas/models/usuario.py:59](../contas/models/usuario.py#L59) |
| | `CadastroComNomeUnicoService` e `ConteudoOrdenadoService` são classes-base concretas: definem o algoritmo de gravação (`salvar`) e deixam para as subclasses o model, o escopo e as regras próprias. `CategoriaService` e `SinalService` herdam da primeira; `ModuloService` e `AulaService`, da segunda | [dicionario/services/cadastro_base.py:9](../dicionario/services/cadastro_base.py#L9), [dicionario/services/categoria.py:6](../dicionario/services/categoria.py#L6), [trilha/services/conteudo.py:10](../trilha/services/conteudo.py#L10), [trilha/services/conteudo.py:65](../trilha/services/conteudo.py#L65) |
| | `CadastroForm` e `PerfilForm` herdam de `DadosPessoaisForm`, com as mesmas regras de nome, e-mail e telefone | [contas/forms/dados_pessoais.py:43](../contas/forms/dados_pessoais.py#L43) |
| | Cada app tem uma exceção base (`ErroDeContas`, `ErroDeDicionario`, `ErroDeTrilha`, `ErroDeQuestionario`, `ErroDeContato`), e as falhas de domínio herdam dela (36 no total) | [contas/exceptions.py:4](../contas/exceptions.py#L4) |
| | Toda view herda de `django.views.View`; um teste garante isso | [contas/tests/test_arquitetura.py](../contas/tests/test_arquitetura.py) |
| **Polimorfismo** | `VideoMp4Validator`, `LegendaVttValidator`, `MaterialValidator` e `ImagemPerfilValidator` sobrescrevem `conteudo_valido`; o Django chama o mesmo `__call__` da base para todos | [core/validadores.py:53](../core/validadores.py#L53) |
| | `CategoriaService.validar_regras` e `SinalService.validar_regras` sobrescrevem o gancho chamado por `salvar` (padrão Template Method); `AulaService.escopo` sobrescreve o escopo da posição | [dicionario/services/categoria.py:15](../dicionario/services/categoria.py#L15), [trilha/services/conteudo.py:77](../trilha/services/conteudo.py#L77) |
| | `AnotacaoView`, `ExcluirAnotacaoView` e `AvaliacaoView` implementam `executar` de formas diferentes; views sobrescrevem `get` e `post`, forms sobrescrevem `clean`, e o Admin sobrescreve `save_model` e as permissões | [trilha/views/participacao.py:47](../trilha/views/participacao.py#L47) |
| | `ImagemPerfilValidator` sobrescreve a propriedade `mensagem` da base | [core/validadores.py:89](../core/validadores.py#L89) |

## Composição

Mixins reaproveitam comportamento sem herança profunda:

- `ValidacaoDeSenhaMixin`: regras de senha do RF001, usadas no cadastro, na redefinição e na troca de senha ([contas/forms/senha.py:15](../contas/forms/senha.py#L15)).
- `SomenteAlunoMixin`: telas do aluno; o administrador recebe 403. É usado pelo perfil e pelo Fale conosco ([contas/views/acesso.py:5](../contas/views/acesso.py#L5)).

## Services e objetos com estado

Os services agrupam as operações de um domínio ([ADR 0001](adr/0001-mvt-com-camada-de-services.md)) e não guardam estado entre uma chamada e outra: cada operação recebe o que precisa e devolve o resultado ou lança uma exceção de domínio. Por isso os métodos são de classe (`@classmethod`), e os services não são instanciados.

O polimorfismo continua valendo. Em `salvar`, a chamada `cls.validar_regras(objeto)` executa a versão da subclasse que foi usada: `SinalService.salvar` aplica as regras de `SinalService`, e `CategoriaService.salvar`, as de `CategoriaService`.

O estado fica nos objetos que o representam:

- **Models:** cada instância de `Usuario`, `Aula` ou `ProgressoAula` é uma linha do banco com os seus dados. `Usuario` ainda herda comportamento do Django, como `check_password`.
- **Objetos de valor:** `Cpf` e `Telefone` são instâncias imutáveis que se validam na criação (`de_texto`) e expõem o valor formatado por propriedades. `TextoNormalizado` guarda a forma de um texto sem acentos nem maiúsculas.
- **Validadores:** cada instância guarda o próprio limite de tamanho (`self.tamanho_maximo`), usado na mensagem e na validação.
- **Forms e views:** o Django cria uma instância a cada requisição, com os dados dela.

## Persistência

- **Django ORM:** 21 tabelas do projeto, com constraints declaradas nos models (`UniqueConstraint`, `CheckConstraint`, índices).
- **SQL:** a trigger e a view do banco são SQL escrito à mão nas migrações, e as contas ficam em `docs/banco/contas.sql` ([ADR 0006](adr/0006-estruturas-do-banco-em-sql.md)).
- **Script do banco:** [docs/banco/ddl.sql](banco/ddl.sql), gerado com `pg_dump`.

## Funcionalidades

São 18 requisitos funcionais completos, cada um com fluxo na tela, persistência e regras de negócio no service. A lista está no [PRD](prd/0001-plataforma-libras-v1.md), e cada requisito tem a sua spec em [docs/specs/](specs/).

## Testes

Os testes automatizados exercitam as classes acima: services, forms, views, constraints do banco e as regras de arquitetura (`python manage.py test`). Um deles confere que as classes abstratas não podem ser instanciadas.

## Skills

As instruções de boas práticas usadas no desenvolvimento estão em [.agents/skills/](../.agents/skills/): Python, Django, segurança (OWASP), PRD, specs e ADRs.