from django import forms
from django.core.exceptions import ValidationError

MINIMO_DE_CARACTERES = 2


class BuscaSinalForm(forms.Form):
    """Filtros da busca no dicionário (RF010). As categorias vêm do service, pela view."""

    busca = forms.CharField(
        label="Buscar palavra",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"type": "search", "placeholder": "Ex.: obrigado"}),
    )
    categoria = forms.TypedChoiceField(
        label="Categoria", required=False, coerce=int, empty_value=None
    )
    favoritos = forms.BooleanField(label="Somente favoritos", required=False)

    def __init__(self, *args, categorias: list[tuple[int, str]] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].choices = [("", "Todas"), *(categorias or [])]

    def clean_busca(self) -> str:
        busca = self.cleaned_data["busca"].strip()
        if busca and len(busca) < MINIMO_DE_CARACTERES:
            raise ValidationError("Digite ao menos 2 caracteres")
        return busca
