from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _criar(self, email: str, password: str | None, **campos) -> "Usuario":
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(email=email.strip().lower(), **campos)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email: str, password: str | None = None, **campos) -> "Usuario":
        campos.setdefault("is_staff", False)
        campos.setdefault("is_superuser", False)
        return self._criar(email, password, **campos)

    def create_superuser(self, email: str, password: str | None = None, **campos) -> "Usuario":
        campos["is_staff"] = True
        campos["is_superuser"] = True
        return self._criar(email, password, **campos)


# As choices ficam no módulo porque a class Meta não enxerga os atributos de Usuario;
# Usuario.Deficiencia e Usuario.ContatoLibras continuam disponíveis pelos aliases.
class Deficiencia(models.TextChoices):
    NAO = "NAO", "Não"
    AUDITIVA = "AUDITIVA", "Sim, deficiência auditiva"
    VISUAL = "VISUAL", "Sim, deficiência visual"
    OUTRA = "OUTRA", "Sim, outra"
    NAO_INFORMAR = "NAO_INFORMAR", "Prefiro não informar"


class ContatoLibras(models.TextChoices):
    NUNCA = "NUNCA", "Nunca tive contato"
    POUCOS_SINAIS = "POUCOS_SINAIS", "Conheço poucos sinais"
    BASICO = "BASICO", "Conheço o básico"
    EXPERIENTE = "EXPERIENTE", "Tenho bastante experiência"


class Usuario(AbstractBaseUser, PermissionsMixin):
    Deficiencia = Deficiencia
    ContatoLibras = ContatoLibras

    nome_completo = models.CharField("nome completo", max_length=120)
    email = models.EmailField("e-mail", max_length=200, unique=True)
    # Nulo só para administradores; com null, vários deles ficam sem CPF sem violar o unique.
    cpf = models.CharField("CPF", max_length=14, unique=True, null=True, blank=True)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)
    telefone = models.CharField(max_length=15, blank=True)
    deficiencia = models.CharField(
        "possui deficiência", max_length=20, choices=Deficiencia, blank=True
    )
    qual_deficiencia = models.CharField("qual deficiência", max_length=120, blank=True)
    contato_libras = models.CharField(
        "teve contato com Libras", max_length=20, choices=ContatoLibras, blank=True
    )
    termos_aceitos_em = models.DateTimeField("termos aceitos em", null=True, blank=True)
    is_active = models.BooleanField("ativo", default=True)
    is_staff = models.BooleanField("administrador", default=False)
    data_cadastro = models.DateTimeField("data de cadastro", default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nome_completo"]

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome_completo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(email=Lower("email")),
                name="usuario_email_minusculo",
            ),
            models.CheckConstraint(
                condition=Q(cpf__isnull=True) | Q(cpf__regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"),
                name="usuario_cpf_formatado",
            ),
            models.CheckConstraint(
                condition=Q(is_staff=True)
                | (
                    Q(
                        cpf__isnull=False,
                        data_nascimento__isnull=False,
                        termos_aceitos_em__isnull=False,
                    )
                    & ~Q(telefone="")
                    & ~Q(deficiencia="")
                    & ~Q(contato_libras="")
                ),
                name="usuario_aluno_completo",
            ),
            models.CheckConstraint(
                condition=Q(qual_deficiencia="") | Q(deficiencia="OUTRA"),
                name="usuario_qual_deficiencia",
            ),
            # Vazio só para administradores; a obrigatoriedade do aluno está em usuario_aluno_completo.
            models.CheckConstraint(
                condition=Q(deficiencia="") | Q(deficiencia__in=Deficiencia.values),
                name="contas_usuario_deficiencia_valido",
            ),
            models.CheckConstraint(
                condition=Q(contato_libras="") | Q(contato_libras__in=ContatoLibras.values),
                name="contas_usuario_contato_libras_valido",
            ),
        ]

    def __str__(self) -> str:
        return self.nome_completo or self.email
