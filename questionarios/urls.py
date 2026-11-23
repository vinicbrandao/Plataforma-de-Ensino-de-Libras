from django.urls import path

from .views import HistoricoView, QuestionarioView

app_name = "questionarios"

urlpatterns = [
    path("aulas/<int:aula_id>/questionario/", QuestionarioView.as_view(), name="responder"),
    path("historico/", HistoricoView.as_view(), name="historico"),
]
