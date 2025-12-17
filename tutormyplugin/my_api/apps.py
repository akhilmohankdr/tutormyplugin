# tutormyplugin/my_api/apps.py
from django.apps import AppConfig
from django.conf import settings
from django.urls import include, path
import importlib

class MyApiConfig(AppConfig):
    name = 'tutormyplugin.my_api'
    verbose_name = 'My Custom API'

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
                if getattr(p, "pattern", None) and "api/myplugin" in str(p.pattern):
                    return

            urlconf.urlpatterns.append(
                path("api/myplugin/", include("tutormyplugin.my_api.urls"))
            )

        except Exception:
            # Never crash LMS because of a plugin
            pass