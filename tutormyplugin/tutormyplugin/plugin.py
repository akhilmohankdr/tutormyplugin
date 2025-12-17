from tutor import hooks

# Plugin metadata
__version__ = "20.0.0"

##########################################################
# Install plugin via pip during image build
##########################################################
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-dockerfile-post-python-requirements",
        """
RUN pip install git+https://github.com/akhilmohankdr/tutormyplugin.git@main
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
INSTALLED_APPS.append('tutormyplugin.my_api')
ALLOWED_HOSTS.append('apps.local.openedx.io')
"""
    )
)

##########################################################
# Register URLs properly
##########################################################
def urls():
    from django.urls import path, include
    return [
        path("api/myplugin/", include("tutormyplugin.my_api.urls")),
    ]

hooks.Filters.LMS_URLS.add_item(urls)
