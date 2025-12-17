from tutor import hooks
import os

__version__ = "20.0.0"
HERE = os.path.abspath(os.path.dirname(__file__))

# Install plugin
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
INSTALLED_APPS.append("tutormyplugin.my_api")
"""
    )
)
