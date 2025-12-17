from tutor import hooks
import os

__version__ = "20.0.0"
HERE = os.path.abspath(os.path.dirname(__file__))

config = {
    "defaults": {
        "VERSION": __version__,
    }
}

##########################################################
# Install plugin via pip during image build
##########################################################
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-dockerfile-post-python-requirements",
        "RUN pip install --no-cache-dir git+https://github.com/akhilmohankdr/tutormyplugin.git@main"
    )
)

##########################################################
# Patch urls.py during build
##########################################################
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-production-settings",
        """
# Myplugin URL configuration
from django.urls import path, include
import sys

# Add myplugin URLs to urlpatterns
if 'tutormyplugin.my_api.urls' not in str(ROOT_URLCONF):
    # Import at runtime to avoid circular imports
    def _add_myplugin_urls():
        from django.conf.urls import url
        from django.urls import path, include
        try:
            import tutormyplugin.my_api.urls
            return [path('api/myplugin/', include('tutormyplugin.my_api.urls'))]
        except ImportError:
            return []
    
    # This will be executed when Django loads
    from django.conf import settings
    if hasattr(settings, 'ROOT_URLCONF'):
        import importlib
        urlconf = importlib.import_module(settings.ROOT_URLCONF)
        if hasattr(urlconf, 'urlpatterns'):
            urlconf.urlpatterns.extend(_add_myplugin_urls())
"""
    )
)

##########################################################
# Add to INSTALLED_APPS
##########################################################
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Add tutormyplugin to INSTALLED_APPS
INSTALLED_APPS.append('tutormyplugin.my_api')
ALLOWED_HOSTS.append('apps.local.openedx.io')
"""
    )
)