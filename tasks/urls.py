from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.check_login),
    path('home', views.home, name='home'),
]