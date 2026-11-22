from django import forms
from django.core.exceptions import ValidationError

from ..exceptions import ErroDeDicionario
from ..models import Categoria, Sinal
from ..services import CategoriaService, SinalService


class CategoriaAdminForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "ativa"]

    def clean_nome(self) -> str:
        nome = self.cleaned_data["nome"]
        try:
            CategoriaService.validar_unico(nome, ignorar_pk=self.instance.pk)
        except ErroDeDicionario as exc:
            raise ValidationError(exc.mensagem) from exc
        return nome

    def clean_ativa(self) -> bool:
        ativa = self.cleaned_data["ativa"]
        try:
            CategoriaService.validar_inativacao(self.instance.pk, ativa=ativa)
        except ErroDeDicionario as exc:
            raise ValidationError(exc.mensagem) from exc
        return ativa


class SinalAdminForm(forms.ModelForm):
    class Meta:
        model = Sinal
        fields = ["termo", "classe_gramatical", "categoria", "descricao_execucao", "video", "ativo"]

    def clean_termo(self) -> str:
        termo = self.cleaned_data["termo"]
        try:
            SinalService.validar_unico(termo, ignorar_pk=self.instance.pk)
        except ErroDeDicionario as exc:
            raise ValidationError(exc.mensagem) from exc
        return termo
