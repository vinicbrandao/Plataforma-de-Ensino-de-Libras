from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=60)
    # Preenchido pelo CategoriaService; garante a unicidade sem acentos nem maiúsculas.
    nome_normalizado = models.CharField(max_length=60, unique=True, editable=False)
    ativa = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
