from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class SomenteAlunoMixin(LoginRequiredMixin):
    """Telas do aluno: o visitante vai ao login e o administrador recebe 403."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
