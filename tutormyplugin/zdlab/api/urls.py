"""Zdlab API main URL patterns
"""

from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('tutormyplugin.zdlab.api.v1.urls', namespace='v1')),
]