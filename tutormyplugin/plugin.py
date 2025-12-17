from tutor import hooks

__version__ = "20.0.0"

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
        """
RUN pip install --no-cache-dir git+https://github.com/akhilmohankdr/tutormyplugin.git@main
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

# Allow apps subdomain
ALLOWED_HOSTS.append('apps.local.openedx.io')
"""
    )
)

##########################################################
# Register URLs
##########################################################
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-urls",
        """
# Add myplugin API routes
from django.urls import path, include
urlpatterns.append(
    path('api/myplugin/', include('tutormyplugin.my_api.urls'))
)
"""
    )
)