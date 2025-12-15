from tutor import hooks

# Plugin metadata
__version__ = "20.0.0"

config = {
    "defaults": {
        "VERSION": __version__,
    }
}

##########################################################
# Install plugin from GitHub during image build
##########################################################

hooks.Filters.OPENEDX_EXTRA_PIP_REQUIREMENTS.add_item(
    "git+https://github.com/akhilmohankdr/tutormyplugin.git@main"
)

##########################################################
# DJANGO: Add to INSTALLED_APPS
##########################################################

hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Custom myplugin app
INSTALLED_APPS.append('tutormyplugin.my_api')

# Allow apps subdomain
ALLOWED_HOSTS.append('apps.local.openedx.io')
"""
    )
)

##########################################################
# URLS: Register API endpoints
##########################################################

hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-urls",
        """
# myplugin API routes
from django.urls import path, include
urlpatterns.append(path('api/myplugin/', include('tutormyplugin.my_api.urls')))
"""
    )
)