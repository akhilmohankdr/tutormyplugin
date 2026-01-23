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

            # Better duplicate check: look for the actual URL pattern
            from django.urls import include
            for p in urlconf.urlpatterns:
                # Check if this pattern already includes our URLs
                if hasattr(p, 'url_patterns'):
                    for sub_p in p.url_patterns:
                        if hasattr(sub_p, 'urlconf_module') and 'zdlab.api' in str(sub_p.urlconf_module):
                            return

            urlconf.urlpatterns.append(
                re_path(r'^zdlab/api/', include('tutormyplugin.zdlab.api.urls'))
            )
            print(f"[ZDLAB] Successfully registered URLs at /zdlab/api/")  # Debug

        except Exception as e:
            print(f"[ZDLAB] Failed to register URLs: {e}")
            # Never crash LMS because of a plugin
            pass