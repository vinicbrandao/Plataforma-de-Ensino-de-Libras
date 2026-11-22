"""Rotas do projeto. Cada app registra as suas com include() e app_name."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from trilha.views import TrilhaView

admin.site.site_header = "Plataforma de Ensino de Libras"
admin.site.site_title = "Área administrativa"
admin.site.index_title = "Área administrativa"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TrilhaView.as_view(), name="inicio"),
    path("", include("contas.urls")),
    path("", include("trilha.urls")),
    path("", include("questionarios.urls")),
    path("dicionario/", include("dicionario.urls")),
]

# Em desenvolvimento, o próprio Django serve os arquivos enviados (vídeos, legendas).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
