from django.urls import path
from . import views

app_name = 'zdlab'  # Change this

urlpatterns = [
    # We'll update this in Phase 2
    path('v1/hello/', views.hello_world, name='hello-world'),
]