"""Zdlab API main URL patterns
"""

from django.urls import include, re_path

urlpatterns = [
    re_path(r'^v1/', include('tutormyplugin.zdlab.api.v1.urls', namespace='v1')),
]