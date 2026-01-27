from django.urls import path
from . import views

app_name = 'v1'  # Change this

urlpatterns = [
    # We'll update this in Phase 2
    path('hello/', views.hello_world, name='hello-world'),
]