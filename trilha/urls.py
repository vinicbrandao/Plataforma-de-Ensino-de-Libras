from django.urls import path

from .views import AulaView

app_name = "trilha"

urlpatterns = [
    path("aulas/<int:aula_id>/", AulaView.as_view(), name="aula"),
]
