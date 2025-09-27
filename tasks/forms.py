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