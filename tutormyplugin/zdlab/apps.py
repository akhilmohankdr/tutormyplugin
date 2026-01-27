from django.apps import AppConfig
from django.conf import settings
from django.urls import include, path
import importlib

class ZdlabAPIConfig(AppConfig):
    name = 'tutormyplugin.zdlab'
    verbose_name = 'Zdlab API'

    def ready(self):
        try:
            urlconf = importlib.import_module(settings.ROOT_URLCONF)
            if not hasattr(urlconf, "urlpatterns"):
                return
            # Check for duplicates
            for p in urlconf.urlpatterns:
                if getattr(p, "pattern", None) and "zdlab/api" in str(p.pattern):
                    return
            # Register from the MAIN zdlab/urls.py (not api/v1/urls.py)
            urlconf.urlpatterns.append(
                path("zdlab/api/", include("tutormyplugin.zdlab.urls"))
            )
            print("[ZDLAB V1] Versioned API registered at /zdlab/api/v1/")
        except Exception as e:
            print(f"[ZDLAB V1] Non-critical error: {e}")