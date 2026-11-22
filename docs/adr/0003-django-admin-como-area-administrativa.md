# ADR 0003: Django Admin como área administrativa

- **Status:** Proposto
- **Data:** 2026-11-21

## Contexto

Os requisitos RF013 a RF016 descrevem uma área administrativa para manter módulos, aulas, materiais, questões, sinais, categorias e usuários. Construir essas telas à mão consumiria boa parte do tempo da versão 1, que deve priorizar a experiência do aluno.

O Django Admin já oferece listagens paginadas, pesquisa, filtros, formulários com validação, registro das alterações (`LogEntry`) e controle de acesso. O RS009 exige que a área seja restrita ao perfil de administrador, sem cadastro público dessas contas.

## Decisão

A área administrativa (RF013 a RF016) é o Django Admin, em `/admin/`.

- Somente usuários com `is_staff` acessam o Admin, e o perfil é verificado pelo próprio Admin a cada requisição. Não há cadastro público de administrador: as contas são criadas com `createsuperuser` ou por outro administrador.
- Os alunos se cadastram pela tela pública e nunca recebem `is_staff`.
- O Admin não ignora as regras de negócio: validações e gravações que dependem de regra, como publicar uma aula, excluir uma aula com progresso ou desativar um aluno, chamam os services ([ADR 0001](0001-mvt-com-camada-de-services.md)).
- Os comportamentos de tela descritos no documento que o Admin não tem, como a confirmação ao clicar em Cancelar (RF013), seguem o padrão do Admin.

## Consequências

- As telas administrativas ficam prontas com pouco código, e o tempo vai para as funcionalidades do aluno.
- O histórico de inclusões, alterações e exclusões vem do `LogEntry` do Admin. Registros que ele não faz, como a consulta ao detalhe de um aluno (RS004) e o login e o logout do administrador (RS009), precisam de código próprio.
- A aparência e o fluxo das telas administrativas não seguem os protótipos do documento.
- Para cumprir RF016, o Admin de usuários é restrito: CPF parcial, sem a informação sobre deficiência, só a situação editável e sem exclusão. Isso exige configuração cuidadosa de `readonly_fields`, `get_fields`, `has_delete_permission` e da pesquisa.
