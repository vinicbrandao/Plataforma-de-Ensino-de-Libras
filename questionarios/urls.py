from django.urls import path

from .views import QuestionarioView

app_name = "questionarios"

urlpatterns = [
    path("aulas/<int:aula_id>/questionario/", QuestionarioView.as_view(), name="responder"),
]
