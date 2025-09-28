from django.contrib import admin
from .models import Project, ProjectModel, Task, TaskCommitRecord, TaskCommentRecord, TrickRecord

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'project_description','project_priority', 'project_creator', 'project_created_time', 'project_updated_time')
    search_fields = ('project_name', 'project_description', 'project_creator__username')
    list_filter = ('project_priority', 'project_created_time', 'project_updated_time')
    ordering = ('-project_priority', '-project_created_time', 'project_name')
    readonly_fields = ('project_created_time', 'project_updated_time')

@admin.register(ProjectModel)
class ProjectModelAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'model_description', 'model_priority', 'model_creator', 'model_belongsto_project_id', 'model_created_time', 'model_updated_time')
    search_fields = ('model_name', 'model_description', 'model_creator__username', 'model_belongsto_project_id__project_name')
    list_filter = ('model_priority', 'model_created_time', 'model_updated_time', 'model_belongsto_project_id')
    ordering = ('-model_priority', '-model_created_time', 'model_name')
    readonly_fields = ('model_created_time', 'model_updated_time')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_title', 'task_description', 'task_type', 'task_status', 'task_priority', 'task_creator', 'task_assigned_to_user_id', 'task_belongsto_model_id', 'task_created_time', 'task_updated_time')
    search_fields = ('task_title', 'task_description', 'task_creator__username', 'task_assigned_to_user_id__username', 'task_belongsto_model_id__model_name')
    list_filter = ('task_type', 'task_status', 'task_priority', 'task_created_time', 'task_updated_time', 'task_belongsto_model_id')
    ordering = ('-task_priority', '-task_created_time', 'task_title')
    readonly_fields = ('task_created_time', 'task_updated_time')

@admin.register(TaskCommitRecord)
class TaskCommitRecordAdmin(admin.ModelAdmin):
    list_display = ('commit_git_hash', 'commit_message', 'commit_is_merged', 'commit_belongsto_task_id', 'commit_submit_time', 'commit_created_time')
    search_fields = ('commit_git_hash', 'commit_message', 'commit_belongsto_task_id__task_title')
    list_filter = ('commit_is_merged', 'commit_submit_time', 'commit_created_time', 'commit_belongsto_task_id')
    ordering = ('-commit_created_time', '-commit_submit_time', 'commit_belongsto_task_id')
    readonly_fields = ('commit_created_time',)

@admin.register(TaskCommentRecord)
class TaskCommentRecordAdmin(admin.ModelAdmin):
    list_display = ('comment_creator', 'comment_belongsto_task_id', 'comment_created_time', 'comment_updated_time')
    search_fields = ('comment_content', 'comment_creator__username', 'comment_belongsto_task_id__task_title')
    list_filter = ('comment_created_time', 'comment_updated_time', 'comment_belongsto_task_id')
    ordering = ('-comment_created_time', 'comment_belongsto_task_id', 'comment_creator')
    readonly_fields = ('comment_created_time', 'comment_updated_time')
    
@admin.register(TrickRecord)
class TrickRecordAdmin(admin.ModelAdmin):
    list_display = ('trick_title', 'trick_content', 'trick_creator', 'trick_created_time', 'trick_updated_time')
    search_fields = ('trick_title', 'trick_content', 'trick_creator__username')
    list_filter = ('trick_created_time', 'trick_updated_time')
    ordering = ('-trick_created_time', 'trick_title')
    readonly_fields = ('trick_created_time', 'trick_updated_time')