from django.urls import path

from .views import FaleConoscoView, MinhasMensagensView

app_name = "contato"

urlpatterns = [
    path("fale-conosco/", FaleConoscoView.as_view(), name="enviar"),
    path("fale-conosco/minhas-mensagens/", MinhasMensagensView.as_view(), name="minhas"),
]
