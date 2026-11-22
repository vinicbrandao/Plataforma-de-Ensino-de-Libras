from django.urls import path

from .views import BuscaView

app_name = "dicionario"

urlpatterns = [
    path("", BuscaView.as_view(), name="busca"),
]
