# Spec 0013: Cadastro de menor de idade (simplificado)

- **Status:** Implementado
- **Requisitos:** RF-105 a RF-110 do [PRD 0001](../prd/0001-plataforma-libras-v1.md) (RF002 do documento de requisitos)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-services.md), [ADR 0005](../adr/0005-emails-no-console-em-desenvolvimento.md)
- **Depende de:** [Spec 0001](0001-fundacao-e-contas.md), [Spec 0012](0012-atualizacao-de-perfil.md) (perfil e histórico)

Quem tem menos de 18 anos se cadastra com os dados do responsável legal, que recebe um aviso por e-mail. Substitui o bloqueio de menores (RF-61).

Simplificações, registradas no PRD:

- A maioridade é calculada pela data de nascimento a cada acesso, sem a rotina diária do documento.
- Não há a preferência do responsável de deixar de receber avisos, que depende dos lembretes (RF011).

## Model `ResponsavelLegal` (`contas/models/responsavel.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `aluno` | `OneToOneField(Usuario, PROTECT, related_name="responsavel")` | |
| `nome` | `CharField(120)` | Regras do nome do RF001 |
| `vinculo` | `CharField(20, choices=VinculoResponsavel)` | `PAI` "Pai", `MAE` "Mãe", `TUTOR` "Tutor ou guardião legal" |
| `cpf` | `CharField(14)` | Formato XXX.XXX.XXX-XX, não único (RF-106) |
| `email` | `EmailField(200)` | Minúsculas, não único |
| `telefone` | `CharField(15)` | Formato (XX) 9XXXX-XXXX |
| `termo_aceito_em` | `DateTimeField` | RF-107 |

Constraints:

- `contas_responsavellegal_vinculo_valido`: os valores das choices.
- `responsavel_cpf_formatado` e `responsavel_email_minusculo`: as mesmas regras de `contas_usuario`.

A regra "CPF do responsável diferente do CPF do aluno" envolve duas tabelas e fica no service.

## Exceções (`contas/exceptions.py`)

| Exceção | Mensagem |
|---|---|
| `ResponsavelObrigatorio` | "Campo obrigatório não preenchido". Substitui `CadastroDeMenorIndisponivel` |
| `CpfDoResponsavelIgualAoDoAluno` | "O CPF do responsável deve ser diferente do CPF do aluno" |
| `ResponsavelSomenteLeitura` | Aluno com 18 anos ou mais tentando alterar o responsável. A view responde 403 |

## Mudanças nos services

### `CadastroService.cadastrar`

Recebe `responsavel: DadosResponsavel | None`.

- Menor de 18 anos sem responsável: `ResponsavelObrigatorio`.
- CPF do responsável igual ao do aluno: `CpfDoResponsavelIgualAoDoAluno`.
- Grava o aluno e o responsável na mesma transação (RF-107).
- Depois do commit, envia ao responsável o e-mail com o nome do aluno e a data do cadastro, sem deficiência nem outros dados sensíveis (RS006).
- Para maiores de 18 anos, o responsável enviado é ignorado.

### `PerfilService`

- `eh_menor(usuario) -> bool`: idade abaixo de 18 na data local de hoje (RF-109).
- `atualizar_responsavel(aluno, dados: DadosResponsavel) -> None`:
  - Só para menor (`ResponsavelSomenteLeitura`).
  - Registra cada campo alterado no histórico como `responsavel.<campo>` (RF-108).
  - Depois do commit, envia o aviso ao e-mail anterior do responsável e, se o e-mail mudou, também ao novo.

## Forms

- `CadastroForm`:
  - Ganha os campos do responsável e o aceite do termo, opcionais no form.
  - O `clean` calcula a idade pela data de nascimento e, para menores, exige todos eles, com "Campo obrigatório não preenchido" e "É necessário confirmar a autorização do responsável".
  - CPF, e-mail e telefone do responsável seguem as mesmas regras e mensagens do aluno, com "CPF do responsável inválido" para o CPF.
- `ResponsavelForm` (perfil, em `contas/forms/perfil.py`): os mesmos campos, menos o termo.
- As regras de nome, e-mail, telefone e CPF ficam em funções de `contas/forms/dados_pessoais.py` (`normalizar_nome`, `normalizar_email`, `normalizar_telefone` e `normalizar_cpf`), usadas pelo aluno e pelo responsável.

## Comportamento

- **Cadastro:** `static/js/cadastro.js` mostra os campos do responsável quando a data de nascimento indica menos de 18 anos e os esconde e limpa quando não indica (RF002). Sem JavaScript, os campos aparecem sempre, com a explicação de que só valem para menores, e o servidor decide pela idade.
- **Perfil:** a seção "Responsável legal" aparece para quem tem responsável. Para o menor, é editável. Para quem já tem 18 anos, aparece só para leitura (RF-109).
- **Perfil:** a alteração é enviada para `contas:responsavel` (`/perfil/responsavel/`, `ResponsavelView`, POST). Para quem já tem 18 anos, a view responde 403.
- **Admin:** o detalhe do aluno mostra o responsável em um inline somente leitura (RF-110), com o CPF parcial, sem permitir alteração.

## Testes

- [x] O menor sem responsável é recusado, e com responsável é cadastrado junto, com a data do termo.
- [x] O CPF do responsável igual ao do aluno é recusado, e o mesmo responsável pode ter dois alunos.
- [x] O responsável recebe o e-mail do cadastro, sem a deficiência do aluno.
- [x] O maior de 18 anos se cadastra sem responsável, e o RF-61 deixa de valer.
- [x] O menor altera o responsável no perfil, com histórico e e-mails ao endereço anterior e ao novo.
- [x] Quem completou 18 anos vê o responsável só para leitura e não consegue alterá-lo.
- [x] O Admin mostra o responsável sem permitir alteração.
