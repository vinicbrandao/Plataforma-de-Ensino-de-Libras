from uuid import uuid4

from django.db import models

from core.validadores import MaterialValidator

from .aula import Aula


def caminho_material(instancia: "MaterialComplementar", nome_enviado: str) -> str:
    # A extensão vem da assinatura do conteúdo, e não do nome enviado (RS012).
    arquivo = instancia.arquivo
    arquivo.seek(0)
    extensao = MaterialValidator.extensao(arquivo.read(16)) or "bin"
    arquivo.seek(0)
    return f"aulas/materiais/{uuid4().hex}.{extensao}"


class MaterialComplementar(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="materiais")
    titulo = models.CharField(
        "título", max_length=100, help_text="Também é o texto alternativo das imagens."
    )
    arquivo = models.FileField(
        upload_to=caminho_material,
        validators=[MaterialValidator()],
        help_text="PDF, JPG ou PNG de até 10 MB.",
    )

    class Meta:
        verbose_name = "material complementar"
        verbose_name_plural = "materiais complementares"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.titulo
