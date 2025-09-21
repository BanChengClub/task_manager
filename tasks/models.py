from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class  Project(models.Model):
    name = models.CharField(max_length=100, verbose_name="项目名称")
    description = models.TextField(blank=True, verbose_name="项目描述")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_projects',
        verbose_name="创建者",
        null=True,  # 允许为空，避免迁移问题
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tasks:project_detail', kwargs={'project_id': self.id})


class ProductModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="机型名称")
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='models',
        verbose_name="所属项目"
    )
    description = models.TextField(blank=True, verbose_name="机型描述")
    created_at = models.DateTimeField(
        default=timezone.now,  # 使用默认值而不是 auto_now_add
        verbose_name="创建时间"
    )

    class Meta:
        verbose_name = "机型"
        verbose_name_plural = "机型"
        ordering = ['name']
        unique_together = ['project', 'name']

    def __str__(self):
        return f"{self.name} ({self.project.name})"


class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('feature', '功能开发'),
        ('bug', 'Bug修复'),
        ('feedback', '反馈任务'),
    ]

    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in-progress', '进行中'),
        ('completed', '已完成'),
    ]

    title = models.CharField(max_length=200, verbose_name="任务标题")
    description = models.TextField(blank=True, verbose_name="任务描述")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name="所属项目")
    model = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='tasks', verbose_name="所属机型")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='feature', verbose_name="任务类型")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="优先级")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    due_date = models.DateField(null=True, blank=True, verbose_name="截止日期")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks', verbose_name="创建者")
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks', null=True,
                                    blank=True, verbose_name="负责人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    source_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='related_tasks', verbose_name="源任务")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'task_id': self.id})

    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return self.due_date < timezone.now().date()
        return False


class Commit(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='commits', verbose_name="关联任务")
    commit_id = models.CharField(max_length=100, verbose_name="Commit ID")
    message = models.TextField(verbose_name="Commit消息")
    commit_date = models.DateField(verbose_name="提交日期")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "提交记录"
        verbose_name_plural = "提交记录"
        ordering = ['-commit_date']

    def __str__(self):
        return f"{self.commit_id} - {self.task.title}"


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name="关联任务")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作者")
    content = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"


class Knowledge(models.Model):
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "知识记录"
        verbose_name_plural = "知识记录"
        ordering = ['-created_at']

    def __str__(self):
        return self.title