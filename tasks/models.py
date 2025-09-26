from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

# Create your models here.

PRIORITY_CHOICES = [
    ('low', '低'),
    ('medium', '中'),
    ('high', '高'),
    ('urgent', '紧急'),
]

# BCClub: 
class Project(models.Model):
    project_name = models.CharField(max_length=100, verbose_name="项目名称")
    project_description = models.TextField(blank=True, verbose_name="项目描述")
    project_priority = models.CharField(max_length=32, choices=PRIORITY_CHOICES, default='medium', verbose_name="项目优先级")
    project_creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects', null=True, blank=True, verbose_name="项目创建者")
    project_created_time = models.DateTimeField(auto_now_add=True, verbose_name="项目创建时间")
    project_updated_time = models.DateTimeField(auto_now=True, verbose_name="项目更新时间")
    
    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ['-project_priority', '-project_created_time', 'project_name']
        
    def __str__(self):
        return self.project_name
    
    def get_absolute_url(self):
        return reverse('tasks:project_detail', kwargs={'project_id': self.id})
    
class ProjectModel(models.Model):
    model_name = models.CharField(max_length=100, verbose_name="机型名称")
    model_description = models.TextField(blank=True, verbose_name="机型描述")
    model_priority = models.CharField(max_length=32, choices=PRIORITY_CHOICES, default='medium', verbose_name="机型优先级")
    model_creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_models', null=True, blank=True, verbose_name="机型创建者")
    model_created_time = models.DateTimeField(auto_now_add=True, verbose_name="机型创建时间")
    model_updated_time = models.DateTimeField(auto_now=True, verbose_name="机型更新时间")
    model_git_repository = models.URLField(blank=True, verbose_name="机型代码仓库")
    model_git_branch = models.CharField(max_length=100, blank=True, verbose_name="机型代码分支")
    model_belongsto_project_id = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='models', verbose_name="所属项目")
    
    class Meta:
        verbose_name = "机型"
        verbose_name_plural = "机型"
        ordering = ['-model_priority', '-model_created_time', 'model_name', 'model_belongsto_project_id']
        
    def __str__(self):
        return f"{self.model_name} ({self.model_belongsto_project_id.project_name})"
    
    def get_absolute_url(self):
        return reverse('tasks:model_detail', kwargs={'model_id': self.id})
    
class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('feature', '功能开发'),
        ('bugfix', 'Bug修复'),
        ('feedback', '横展反馈'),
        ("documentation", "文档编写"),
        ("optimization", "性能优化"),
        ("testing", "测试"),
        ("research", "功能调研"),
        ("other", "其他"),
    ]
    
    TASK_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('on_hold', '暂停'),
        ('cancelled', '已取消'),
    ]
    
    task_title = models.CharField(max_length=100, verbose_name="任务标题")
    task_description = models.TextField(blank=True, verbose_name="任务描述")
    task_priority = models.CharField(max_length=32, choices=PRIORITY_CHOICES, default='medium', verbose_name="任务优先级")
    task_creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks', null=True, blank=True, verbose_name="任务创建者")
    task_created_time = models.DateTimeField(auto_now_add=True, verbose_name="任务创建时间")
    task_updated_time = models.DateTimeField(auto_now=True, verbose_name="任务更新时间")
    task_start_time = models.DateTimeField(null=True, blank=True, verbose_name="任务开始时间")
    task_end_time = models.DateTimeField(null=True, blank=True, verbose_name="任务结束时间")
    task_deadline = models.DateTimeField(null=True, blank=True, verbose_name="任务截止时间")
    task_status = models.CharField(max_length=32, choices=TASK_STATUS_CHOICES, default='pending', verbose_name="任务状态")
    task_type = models.CharField(max_length=32, choices=TASK_TYPE_CHOICES, default='feature', verbose_name="任务类型")
    task_belongsto_model_id = models.ForeignKey(ProjectModel, on_delete=models.CASCADE, related_name='tasks', verbose_name="所属机型")
    task_source_task_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_tasks', verbose_name="源任务ID")
    task_assigned_to_user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="负责人")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ['-task_priority', '-task_created_time', 'task_title', 'task_belongsto_model_id', 'task_status', 'task_deadline', 'task_assigned_to_user_id', 'task_type', 'task_creator']
        
    def __str__(self):
        return f"{self.task_title} ({self.task_belongsto_model_id.model_name})"
    
    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'task_id': self.id})
    
    def is_overdue(self):
        if self.task_deadline and self.task_status != 'completed':
            return timezone.now() > self.task_deadline
        return False
    
