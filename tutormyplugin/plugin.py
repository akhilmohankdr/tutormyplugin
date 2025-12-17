from tutor import hooks
import os

__version__ = "20.0.0"

config = {
    "defaults": {
        "VERSION": __version__,
    }
}

# Install plugin via pip during image build
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-dockerfile-post-python-requirements",
        "RUN pip install --no-cache-dir git+https://github.com/akhilmohankdr/tutormyplugin.git@main"
    )
)

# Add to INSTALLED_APPS
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

# DIRECT URL INJECTION - This WILL work
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-production-settings",
        """
# Myplugin URL registration
import sys
def _register_myplugin_urls():
    try:
        from django.conf import settings
        from django.urls import path, include
        import importlib
        
        # Get the actual URLconf module
        urlconf_module = importlib.import_module(settings.ROOT_URLCONF)
        
        # Check if already registered
        if hasattr(urlconf_module, 'urlpatterns'):
            already_has = any('myplugin' in str(p) for p in urlconf_module.urlpatterns)
            if not already_has:
                import tutormyplugin.my_api.urls
                urlconf_module.urlpatterns.append(
                    path('api/myplugin/', include('tutormyplugin.my_api.urls'))
                )
                print("✅ Myplugin URLs registered in production settings")
    except Exception as e:
        print(f"❌ Myplugin URL registration error: {e}")

# Register immediately when settings are imported
_register_myplugin_urls()
"""
    )
)

# Same for development settings
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-development-settings",
        """
# Myplugin URL registration
import sys
def _register_myplugin_urls():
    try:
        from django.conf import settings
        from django.urls import path, include
        import importlib
        
        urlconf_module = importlib.import_module(settings.ROOT_URLCONF)
        
        if hasattr(urlconf_module, 'urlpatterns'):
            already_has = any('myplugin' in str(p) for p in urlconf_module.urlpatterns)
            if not already_has:
                import tutormyplugin.my_api.urls
                urlconf_module.urlpatterns.append(
                    path('api/myplugin/', include('tutormyplugin.my_api.urls'))
                )
                print("✅ Myplugin URLs registered in development settings")
    except Exception as e:
        print(f"❌ Myplugin URL registration error: {e}")

_register_myplugin_urls()
"""
    )
)