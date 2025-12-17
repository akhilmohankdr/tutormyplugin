# Add myplugin API URLs
from django.urls import path, include

urlpatterns += [
    path("api/myplugin/", include("tutormyplugin.my_api.urls")),
]
