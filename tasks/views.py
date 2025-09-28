from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime

from .models import Task, Project, ProjectModel, TaskCommitRecord, TaskCommentRecord, TrickRecord
from .forms import ProjectForm

# Create your views here.

# BCClub: 检测是否登录的视图
def check_login(request):
    """
    检查用户登录状态并跳转
    - 未登录：跳转到登录页面
    - 已登录：跳转到主页
    """
    if request.user.is_authenticated:
        # 已登录，跳转到主页
        return redirect('tasks:home')
    else:
        # 未登录，跳转到登录页面
        return redirect('login')

def loginout_view(request):
    logout(request)
    return redirect('login')

# BCClub: 用户注册视图
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # 保存用户并直接获取用户对象
            user = form.save()
            login(request, user)
            return redirect('tasks:home')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

# BCClub: 主页视图
@login_required
def home(request):
    # 获取统计信息
    total_tasks = Task.objects.filter(task_assigned_to_user_id=request.user).count()
    pending_tasks = Task.objects.filter(task_assigned_to_user_id=request.user, task_status='pending').count()
    in_progress_tasks = Task.objects.filter(task_assigned_to_user_id=request.user, task_status='in-progress').count()
    completed_tasks = Task.objects.filter(task_assigned_to_user_id=request.user, task_status='completed').count()
    on_hold_tasks = Task.objects.filter(task_assigned_to_user_id=request.user, task_status='on-hold').count()
    cancelled_tasks = Task.objects.filter(task_assigned_to_user_id=request.user, task_status='cancelled').count()

    # 获取今天到期的任务
    today = timezone.now().date()
    today_tasks = Task.objects.filter(
        task_assigned_to_user_id=request.user,
        task_deadline=today,
        task_status__in=['pending', 'in-progress', 'on-hold']
    )

    # 获取最近任务
    recent_tasks = Task.objects.filter(task_assigned_to_user_id=request.user).order_by('-task_created_time')[:10]

    # 获取即将到期的任务
    due_soon_tasks = Task.objects.filter(
        task_assigned_to_user_id=request.user,
        task_deadline__gte=today,
        task_deadline__lte=today + timedelta(days=7),
        task_status__in=['pending', 'in-progress', 'on-hold']
    )

    # 获取项目统计
    projects = Project.objects.annotate(
        task_count=Count('tasks', filter=Q(tasks__task_assigned_to_user_id=request.user)),
        completed_count=Count('tasks', filter=Q(tasks__task_assigned_to_user_id=request.user, tasks__task_status='completed'))
    )

    # 获取所有项目用于侧边栏
    all_projects = Project.objects.all()[:6]  # 只取前6个项目显示在侧边栏

    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'on_hold_tasks': on_hold_tasks,
        'completed_tasks': completed_tasks,
        'today_tasks': today_tasks,
        'recent_tasks': recent_tasks,
        'due_soon_tasks': due_soon_tasks,
        'projects': projects,
        'all_projects': all_projects,  # 传递给侧边栏
    }

    return render(request, 'tasks/home.html', context)

@login_required
def task_list(request):
    tasks = Task.objects.filter(task_assigned_to_user_id=request.user).order_by('-task_created_time')
    # 处理并合并所有筛选条件
    status_filter = request.GET.get('task_status')
    project_filter = request.GET.get('project_id')
    model_filter = request.GET.get('model_id')
    search_query = request.GET.get('q')

    if status_filter:
        tasks = tasks.filter(task_status=status_filter)
    if project_filter:
        tasks = tasks.filter(task_belongsto_project_id=project_filter)
    if model_filter:
        tasks = tasks.filter(task_belongsto_model_id=model_filter)
    if search_query:
        tasks = tasks.filter(Q(task_title__icontains=search_query) | Q(task_description__icontains=search_query))
    
    # 获取所有项目用于筛选
    all_projects = Project.objects.all()
    all_models = ProjectModel.objects.all()

    context = {
        'tasks': tasks,
        'all_projects': all_projects,
        'all_models': all_models,
        'status_filter': status_filter,
        'project_filter': project_filter,
        'model_filter': model_filter,
        'search_query': search_query or '',
    }

    return render(request, 'tasks/task_list.html', context)

@login_required
def calendar_view(request):

    # 获取请求的年份和月份，默认为当前
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    # 计算该月的第一天和最后一天
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # 获取该月内的任务
    tasks = Task.objects.filter(
        task_assigned_to_user_id=request.user,
        task_deadline__gte=first_day,
        task_deadline__lte=last_day
    )

    # 按照日期组织任务
    tasks_by_date = {}
    for task in tasks:
        day = task.task_deadline.day
        if day not in tasks_by_date:
            tasks_by_date[day] = []
        tasks_by_date[day].append(task)

    context = {
        'tasks_by_date': tasks_by_date,
        'first_day': first_day,
        'last_day': last_day,
        'current_year': year,
        'current_month': month,
        'prev_year': (year - 1) if month == 1 else year,
        'prev_month': 12 if month == 1 else (month - 1),
        'next_year': (year + 1) if month == 12 else year,
        'next_month': 1 if month == 12 else (month + 1),
    }

    return render(request, 'tasks/calendar.html', context)

@login_required
def project_list(request):
    projects = Project.objects.all()

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '项目创建成功')
            return redirect('tasks:project_list')
    else:
        form = ProjectForm()

    context = {
        'projects': projects,
        'form': form,
    }

    return render(request, 'tasks/project_list.html', context)

@login_required
def tricks_view(request):
    tricks = TrickRecord.objects.all().order_by('-trick_created_time')

    context = {
        'tricks': tricks,
    }

    return render(request, 'tasks/tricks.html', context)