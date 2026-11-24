# Plataforma de Ensino de Libras

Aplicação web para ensino de Libras, com trilha de aulas em vídeo, questionários e dicionário de sinais. É um projeto acadêmico de Engenharia de Software, também avaliado em Laboratório de Programação Orientada a Objetos e Laboratório de Banco de Dados.

- Requisitos completos: [docs/requisitos.md](docs/requisitos.md)
- Escopo da versão 1 (PRD): [docs/prd.md](docs/prd.md), que leva a [docs/prd/0001-plataforma-libras-v1.md](docs/prd/0001-plataforma-libras-v1.md)
- Arquitetura: [docs/arquitetura.md](docs/arquitetura.md)
- Especificações: [docs/specs/](docs/specs/) e decisões: [docs/adr/](docs/adr/)
- Pilares de POO no código: [docs/poo.md](docs/poo.md)
- Banco de dados (Lab. BD): [docs/banco/](docs/banco/entrega-lab-bd.md)
- Skills usadas no desenvolvimento: [.agents/skills/](.agents/skills/)
- Estado atual e próximos passos: [docs/state.md](docs/state.md)

Tecnologias: Python 3.12 ou mais recente, Django 6.1 e PostgreSQL (testado com a versão 18).

## Como rodar no Windows

Os comandos abaixo são para o PowerShell, na pasta do projeto.

### 1. Ambiente virtual e dependências

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear o `Activate.ps1`, rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` uma vez. Outra saída é não ativar o venv e usar `.venv\Scripts\python` no lugar de `python` em todos os comandos.

### 2. Banco de dados

Com o PostgreSQL instalado e o serviço rodando, crie o usuário e o banco. O `psql` pede a senha do usuário `postgres`, definida na instalação. Se o comando não for encontrado, use o caminho completo, como `& "C:\Program Files\PostgreSQL\18\bin\psql.exe"`.

```powershell
psql -U postgres -c "CREATE ROLE libras_owner WITH LOGIN CREATEDB PASSWORD 'troque-esta-senha';"
psql -U postgres -c "CREATE DATABASE plataforma_libras OWNER libras_owner ENCODING 'UTF8' TEMPLATE template0;"
```

A permissão `CREATEDB` é necessária porque `python manage.py test` cria um banco temporário de testes.

### 3. Variáveis de ambiente

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Abra o `.env` e preencha `DJANGO_SECRET_KEY` com o valor gerado e `POSTGRES_PASSWORD` com a senha escolhida no passo 2. O `.env` não vai para o Git.

### 4. Tabelas, administrador e servidor

O `createsuperuser` pede e-mail, nome completo e senha. As contas de administrador são criadas só por esse comando: não há cadastro público de administrador. Alunos se cadastram em `/cadastro/` e entram com e-mail ou CPF.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Site: <http://127.0.0.1:8000/>
- Área administrativa (Django Admin): <http://127.0.0.1:8000/admin/>

Em desenvolvimento, os e-mails (como o de recuperação de senha) aparecem no terminal do `runserver`, e não são enviados de verdade.

### 5. Conteúdo inicial para a demonstração (opcional)

O comando abaixo cadastra 3 módulos com 2 aulas cada, 18 questões, 3 categorias e 15 sinais, pelas mesmas regras do Admin. Os vídeos e as legendas vêm da pasta `amostras/`, com os nomes listados em [amostras/LEIA-ME.md](amostras/LEIA-ME.md).

```powershell
python manage.py criar_conteudo_inicial
```

- Pode rodar várias vezes: nada é duplicado.
- Se faltar arquivo, o comando cria o que der, deixa não publicada a aula sem vídeo ou legenda, não cria o sinal sem vídeo e lista no terminal o que falta. Depois de colocar os arquivos, rode de novo.
- Outra pasta: `python manage.py criar_conteudo_inicial --pasta C:\caminho\das\amostras`.
- As descrições da execução dos sinais ficam em branco, para a equipe completar pelo Admin.

## Banco de dados: contas e entrega de Lab. BD

O material de Laboratório de Banco de Dados está em [docs/banco/](docs/banco/entrega-lab-bd.md). As contas `libras_app` e `libras_relatorio` são criadas uma vez pelo superusuário `postgres`:

```powershell
psql -U postgres -h localhost -d plataforma_libras -f docs/banco/contas.sql
psql -U postgres -h localhost -d plataforma_libras -f docs/banco/verificacao.sql
```

O papel dono do banco se chama `libras_owner` ([ADR 0010](docs/adr/0010-dono-do-banco-libras-owner.md)). Se o seu banco foi criado antes, com o papel `plataforma_libras`, renomeie-o uma vez e troque `POSTGRES_USER` no `.env` para `libras_owner`:

```powershell
psql -U postgres -h localhost -d postgres -c "ALTER ROLE plataforma_libras RENAME TO libras_owner;"
```

## Verificações

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check
```
