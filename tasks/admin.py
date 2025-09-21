from django.contrib import admin
from .models import Project, ProductModel, Task, Commit, Comment, Knowledge

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'created_by')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'description', 'created_at')
    search_fields = ('name', 'project__name', 'description')
    list_filter = ('project', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'model', 'task_type', 'priority', 'status', 'due_date', 'created_by', 'assigned_to', 'created_at')
    list_filter = ('project', 'model', 'task_type', 'priority', 'status', 'created_at')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('commit_id', 'task', 'commit_date', 'created_at')
    list_filter = ('commit_date', 'created_at')
    search_fields = ('commit_id', 'message', 'task__title')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'task__title', 'author__username')

@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content', 'created_by__username')