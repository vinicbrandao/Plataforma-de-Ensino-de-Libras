from django.urls import path

from .views import CadastroView, EntrarView, SairView

app_name = "contas"

urlpatterns = [
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("entrar/", EntrarView.as_view(), name="entrar"),
    path("sair/", SairView.as_view(), name="sair"),
]
