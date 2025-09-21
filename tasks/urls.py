from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('knowledge/', views.knowledge_base, name='knowledge'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('models/<int:model_id>/edit/', views.model_edit, name='model_edit'),
    path('models/<int:model_id>/delete/', views.model_delete, name='model_delete'),
    path('api/projects/<int:project_id>/models/', views.project_models_api, name='project_models_api'),
    path('debug/', views.debug_info, name='debug_info'),
]