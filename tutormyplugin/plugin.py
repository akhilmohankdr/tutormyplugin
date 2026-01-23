from tutor import hooks
import os

__version__ = "20.0.0"
HERE = os.path.abspath(os.path.dirname(__file__))

# Install plugin from GitHub
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-dockerfile-post-python-requirements",
        "RUN pip install --no-cache-dir git+https://github.com/akhilmohankdr/tutormyplugin.git@main"
    )
)

# Add BOTH APIs to INSTALLED_APPS
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
INSTALLED_APPS.append("tutormyplugin.my_api")
INSTALLED_APPS.append("tutormyplugin.zdlab.api")
"""
    )
)

# Register zdlab URLs via Tutor hook
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-urls",
        """
# Add zdlab API URLs
from django.urls import include, re_path
urlpatterns += [
    re_path(r'^zdlab/api/v1/', include('tutormyplugin.zdlab.api.v1.urls')),
]
"""
    )
)