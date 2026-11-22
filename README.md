# Plataforma de Ensino de Libras

Aplicação web para ensino de Libras, com trilha de aulas em vídeo, questionários e dicionário de sinais. É um projeto acadêmico de Engenharia de Software, também avaliado em Laboratório de Programação Orientada a Objetos e Laboratório de Banco de Dados.

- Requisitos completos: [docs/requisitos.md](docs/requisitos.md)
- Escopo da versão 1: [docs/prd/0001-plataforma-libras-v1.md](docs/prd/0001-plataforma-libras-v1.md)
- Arquitetura: [docs/arquitetura.md](docs/arquitetura.md)
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
psql -U postgres -c "CREATE ROLE plataforma_libras WITH LOGIN CREATEDB PASSWORD 'troque-esta-senha';"
psql -U postgres -c "CREATE DATABASE plataforma_libras OWNER plataforma_libras ENCODING 'UTF8' TEMPLATE template0;"
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

## Verificações

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check
```
