from django.urls import path

from .views import (
    CadastroView,
    ConfirmarEmailView,
    EntrarView,
    EsqueciSenhaView,
    FotoView,
    PerfilView,
    RedefinirSenhaView,
    ResponsavelView,
    SairView,
    TrocaSenhaView,
)

app_name = "contas"

urlpatterns = [
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("entrar/", EntrarView.as_view(), name="entrar"),
    path("sair/", SairView.as_view(), name="sair"),
    path("senha/esqueci/", EsqueciSenhaView.as_view(), name="esqueci_senha"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("perfil/foto/", FotoView.as_view(), name="foto"),
    path("perfil/senha/", TrocaSenhaView.as_view(), name="trocar_senha"),
    path("perfil/responsavel/", ResponsavelView.as_view(), name="responsavel"),
    path("perfil/confirmar-email/<str:codigo>/", ConfirmarEmailView.as_view(), name="confirmar_email"),
    path("senha/redefinir/", RedefinirSenhaView.as_view(), name="redefinir_senha"),
    path("senha/redefinir/<str:codigo>/", RedefinirSenhaView.as_view(), name="redefinir_senha_link"),
]
