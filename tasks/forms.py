from django import forms
from .models import Project, Task, ProjectModel, TaskCommitRecord, TaskCommentRecord, TrickRecord

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name', 'project_description', 'project_priority']
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control'}),
            'project_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'project_priority': forms.Select(attrs={'class': 'form-control'}),
        }

class ProjectModelForm(forms.ModelForm):
    class Meta:
        model = ProjectModel
        fields = ['model_name', 'model_description', 'model_priority', 'model_creator', 'model_git_repository', 'model_git_branch']
        exclude = ['model_created_time', 'model_updated_time', 'model_belongsto_project_id']
        widgets = {
            'model_name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'model_priority': forms.Select(attrs={'class': 'form-control'}),
            'model_creator': forms.Select(attrs={'class': 'form-control'}),
            'model_git_repository': forms.URLInput(attrs={'class': 'form-control'}),
            'model_git_branch': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['task_title', 'task_description', 'task_priority', 'task_status', 'task_type', 'task_assigned_to_user_id', 'task_belongsto_project_id', 'task_belongsto_model_id', 'task_source_task_id', 'task_deadline']
        widgets = {
            'task_title': forms.TextInput(attrs={'class': 'form-control'}),
            'task_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'task_priority': forms.Select(attrs={'class': 'form-control'}),
            'task_status': forms.Select(attrs={'class': 'form-control'}),
            'task_type': forms.Select(attrs={'class': 'form-control'}),
            'task_assigned_to_user_id': forms.Select(attrs={'class': 'form-control'}),
            'task_belongsto_project_id': forms.Select(attrs={'class': 'form-control'}),
            'task_belongsto_model_id': forms.Select(attrs={'class': 'form-control'}),
            'task_source_task_id': forms.Select(attrs={'class': 'form-control'}),
            'task_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class CommitForm(forms.ModelForm):
    class Meta:
        model = TaskCommitRecord
        fields = ['commit_git_hash', 'commit_message', 'commit_url', 'commit_submit_time', 'commit_is_merged', 'commit_merge_request_url']
        widgets = {
            'commit_git_hash': forms.TextInput(attrs={'class': 'form-control'}),
            'commit_message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'commit_url': forms.URLInput(attrs={'class': 'form-control'}),
            'commit_submit_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'commit_is_merged': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'commit_merge_request_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = TaskCommentRecord
        fields = ['comment_content']
        widgets = {
            'comment_content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '添加评论...'}),
        }

class TrickForm(forms.ModelForm):
    class Meta:
        model = TrickRecord
        fields = ['trick_title', 'trick_content']
        widgets = {
            'trick_title': forms.TextInput(attrs={'class': 'form-control'}),
            'trick_content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }