# tutormyplugin/my_api/urls.py
from django.urls import path
from . import views

app_name = 'my_api'

urlpatterns = [
    path('hello/', views.hello_world, name='hello-world'),
    path('test/', views.test_api, name='test-api'),
    path('getuser/',views.user_list,name ="get_user"),
    path('stats/', views.user_stats, name='user-stats'),
]