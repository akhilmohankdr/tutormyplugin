from django.apps import AppConfig
from django.conf import settings
from django.urls import include, path
import importlib

class ZdlabAPIConfig(AppConfig):
    name = 'tutormyplugin.zdlab'  # Change this
    verbose_name = 'Zdlab API'    # Change this

    def ready(self):
        try:
            urlconf = importlib.import_module(settings.ROOT_URLCONF)
            if not hasattr(urlconf, "urlpatterns"):
                return
            # Avoid duplicate registration
            for p in urlconf.urlpatterns:
                if getattr(p, "pattern", None) and "zdlab/api" in str(p.pattern):
                    return
            # 🔑 CRITICAL: Register at the NEW path
            urlconf.urlpatterns.append(
                path("zdlab/api/", include("tutormyplugin.zdlab.urls"))
            )
        except Exception as e:
            # Never crash LMS
            print(f"[ZDLAB] URL registration failed (non-critical): {e}")