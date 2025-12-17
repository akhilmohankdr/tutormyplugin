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

##########################################################
# Register URLs - Use the init task approach
##########################################################
hooks.Filters.CLI_DO_INIT_TASKS.add_item(
    ("lms", ("myplugin", "urls"))
)

# Add URL configuration via template
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    os.path.join(HERE, "templates")
)