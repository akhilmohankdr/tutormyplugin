from django.apps import AppConfig
from django.conf import settings
from django.urls import include, re_path
import importlib

class ZdlabAPIConfig(AppConfig):
    """
    Configuration class for the Zdlab API Django app.
    """
    name = 'tutormyplugin.zdlab.api'
    label = 'zdlab_api'
    verbose_name = "Zdlab API"

    def ready(self):
        """
        Register plugin URLs safely when Django is ready.
        """
        try:
            urlconf = importlib.import_module(settings.ROOT_URLCONF)

            if not hasattr(urlconf, "urlpatterns"):
                return

            # Avoid duplicate registration
            for p in urlconf.urlpatterns:
                if getattr(p, "pattern", None) and "zdlab/api" in str(p.pattern):
                    return

            urlconf.urlpatterns.append(
                re_path(r'^zdlab/api/', include('tutormyplugin.zdlab.api.urls'))
            )

        except Exception:
            # Never crash LMS because of a plugin
            pass