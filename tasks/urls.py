from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.check_login, name='check_login'),
    path('home', views.home, name='home'),
    path('projects/', views.project_list, name='project_list'),
    path('project/create/', views.project_create, name='project_create'),
    path('project/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('task_list', views.task_list, name='task_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('tricks/', views.tricks_view, name='tricks'),
]