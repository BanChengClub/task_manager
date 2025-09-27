from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.check_login, name='check_login'),
    path('home', views.home, name='home'),
    path('task_list', views.task_list, name='task_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('projects/', views.project_list, name='project_list'),
    path('tricks/', views.tricks_view, name='tricks'),
]