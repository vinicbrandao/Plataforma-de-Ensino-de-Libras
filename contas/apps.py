from django.apps import AppConfig


class ContasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contas"
    verbose_name = "Contas"

    def ready(self) -> None:
        from . import receptores  # noqa: F401  (conecta os receptores de sinais)
