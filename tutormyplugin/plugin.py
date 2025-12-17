from tutor import hooks

__version__ = "20.0.0"

config = {
    "defaults": {
        "VERSION": __version__,
    }
}

##########################################################
# DJANGO: Add to INSTALLED_APPS
##########################################################

hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Register myplugin Django app
if 'tutormyplugin.my_api' not in INSTALLED_APPS:
    INSTALLED_APPS.append('tutormyplugin.my_api')

# Register myplugin URLs
from django.urls import include, path

def _add_myplugin_urls(urlpatterns):
    urlpatterns.append(
        path("api/myplugin/", include("tutormyplugin.my_api.urls"))
    )
    return urlpatterns

ROOT_URLCONF_PATCHES = globals().get("ROOT_URLCONF_PATCHES", [])
ROOT_URLCONF_PATCHES.append(_add_myplugin_urls)
"""
    )
)
