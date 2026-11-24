from django.urls import path

from .views import BuscaView, FavoritoView

app_name = "dicionario"

urlpatterns = [
    path("", BuscaView.as_view(), name="busca"),
    path("sinais/<int:sinal_id>/favorito/", FavoritoView.as_view(), name="favoritar"),
]
