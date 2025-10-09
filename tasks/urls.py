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
    path('project/<int:project_id>/models/', views.project_models, name='project_models'),
    path('models/<int:model_id>/edit/', views.model_edit, name='model_edit'),
    path('models/<int:model_id>/delete/', views.model_delete, name='model_delete'),
    path('task_list', views.task_list, name='task_list'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('tricks/', views.tricks_view, name='tricks'),
]