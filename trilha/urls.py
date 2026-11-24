from django.urls import path

from .views import AnotacaoView, AulaView, AvaliacaoView, ExcluirAnotacaoView

app_name = "trilha"

urlpatterns = [
    path("aulas/<int:aula_id>/", AulaView.as_view(), name="aula"),
    path("aulas/<int:aula_id>/anotacao/", AnotacaoView.as_view(), name="salvar_anotacao"),
    path("aulas/<int:aula_id>/anotacao/excluir/", ExcluirAnotacaoView.as_view(), name="excluir_anotacao"),
    path("aulas/<int:aula_id>/avaliacao/", AvaliacaoView.as_view(), name="avaliar"),
]
