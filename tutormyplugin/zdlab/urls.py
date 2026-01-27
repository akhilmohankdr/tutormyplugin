"""Main URL router for the Zdlab API."""
from django.urls import include, path

urlpatterns = [
    path('v1/', include('tutormyplugin.zdlab.api.v1.urls')),
]