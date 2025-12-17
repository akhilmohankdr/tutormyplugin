from django.urls import include, path

def plugin_urls():
    return [
        path("api/myplugin/", include("tutormyplugin.my_api.urls")),
    ]
