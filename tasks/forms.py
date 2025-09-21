from django import forms
from .models import Task, Commit, Comment, Project, ProductModel


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'project', 'model',
            'task_type', 'priority', 'status', 'due_date', 'assigned_to', 'source_task'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-select', 'id': 'id_project'}),
            'model': forms.Select(attrs={'class': 'form-select', 'id': 'id_model'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'source_task': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置初始值
        self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.order_by('username')
        self.fields['source_task'].queryset = self.fields['source_task'].queryset.order_by('-created_at')

        # 如果实例已存在，限制机型选择为所选项目的机型
        if self.instance and self.instance.pk:
            self.fields['model'].queryset = ProductModel.objects.filter(project=self.instance.project)
        else:
            # 对于新任务，检查是否有项目数据传入
            if 'project' in self.data:
                try:
                    project_id = int(self.data.get('project'))
                    self.fields['model'].queryset = ProductModel.objects.filter(project_id=project_id)
                except (ValueError, TypeError):
                    # 如果项目ID无效，设置为空查询集
                    self.fields['model'].queryset = ProductModel.objects.none()
            else:
                # 如果没有项目数据，设置为空查询集
                self.fields['model'].queryset = ProductModel.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        model = cleaned_data.get('model')

        # 确保所选机型属于所选项目
        if project and model and model.project != project:
            raise forms.ValidationError("所选机型不属于当前项目，请重新选择")

        return cleaned_data


class CommitForm(forms.ModelForm):
    class Meta:
        model = Commit
        fields = ['commit_id', 'message', 'commit_date']
        widgets = {
            'commit_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'commit_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '输入评论内容...',
                'class': 'form-control'
            }),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class ProductModelForm(forms.ModelForm):
    class Meta:
        model = ProductModel
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 移除项目字段，因为我们会在视图中设置
        if 'project' in self.fields:
            del self.fields['project']