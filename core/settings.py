"""
Configurações do projeto Plataforma de Ensino de Libras.

Gerado com 'django-admin startproject' (Django 6.1.3) e ajustado para ler
segredos e credenciais do arquivo .env. Referência:
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Lê o .env da raiz do projeto. Variáveis já definidas no ambiente têm prioridade.
load_dotenv(BASE_DIR / ".env")


def _env_bool(nome: str, padrao: bool = False) -> bool:
    return os.environ.get(nome, str(padrao)).strip().lower() in {"1", "true", "sim", "yes"}


def _env_lista(nome: str) -> list[str]:
    return [item.strip() for item in os.environ.get(nome, "").split(",") if item.strip()]


# Segurança
# https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

DEBUG = _env_bool("DJANGO_DEBUG")

# Sem a variável, o desenvolvimento usa uma chave temporária, e as sessões caem ao
# reiniciar o servidor. Fora dele, a chave fica vazia e o Django se recusa a usá-la.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (get_random_secret_key() if DEBUG else "")

ALLOWED_HOSTS = _env_lista("DJANGO_ALLOWED_HOSTS")


# Aplicações

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "contas",
    "dicionario",
    "trilha",
    "questionarios",
    "contato",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "contas.middleware.SemCacheParaAutenticadosMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Banco de dados (ADR 0002)
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "plataforma_libras"),
        "USER": os.environ.get("POSTGRES_USER", "libras_owner"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Validação de senhas
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "contas.validadores.LetrasENumerosValidator"},
]


# Autenticação e sessão (spec 0001)

AUTH_USER_MODEL = "contas.Usuario"

AUTHENTICATION_BACKENDS = ["contas.backends.EmailOuCpfBackend"]

LOGIN_URL = "contas:entrar"

LOGIN_REDIRECT_URL = "inicio"

# A sessão expira após 30 minutos sem requisições (RS010).
SESSION_COOKIE_AGE = 30 * 60

SESSION_SAVE_EVERY_REQUEST = True


# Internacionalização

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# Arquivos estáticos e enviados

STATIC_URL = "static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"


# E-mail (ADR 0005): em desenvolvimento, as mensagens são exibidas no terminal.
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "nao-responda@localhost")
