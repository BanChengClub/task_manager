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

from .models import PRIORITY_CHOICES, Task, Project, ProjectModel, TaskCommitRecord, TaskCommentRecord, TrickRecord
from .forms import ProjectForm, ProjectModelForm, TaskForm, CommentForm, TrickForm, CommitForm

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
def project_list(request):
    projects = Project.objects.all()

    context = {
        'projects': projects,
    }

    return render(request, 'tasks/project_list.html', context)

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.project_creator = request.user
            project.save()
            messages.success(request, '项目创建成功')
            return redirect('tasks:project_list')
    else:
        form = ProjectForm()
    
    context = {
        'form': form,
        'title': '创建新项目',
    }
    
    return render(request, 'tasks/project_create.html', context)

@login_required
def project_edit(request, project_id):
    # 如果是管理员或创建者，则允许编辑
    project = get_object_or_404(Project, id=project_id)
    # 检查当前用户是否为管理员或创建者
    if not (request.user == project.project_creator or request.user.is_superuser):
        messages.error(request, '您没有权限编辑该项目。')
        return redirect('tasks:project_list')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, '项目更新成功')
            return redirect('tasks:project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form,
        'title': '编辑项目',
        'project': project,
    }
    
    return render(request, 'tasks/project_create.html', context)

@login_required
def project_detail(request, project_id):
    # 如果是管理员或创建者，则允许编辑和删除
    project = get_object_or_404(Project, id=project_id)
    project_form = ProjectForm(instance=project)  # Ensure project_form is always defined

    if request.method == 'POST':
        if 'edit_project' in request.POST:
            form = ProjectForm(request.POST, instance=project)
            if form.is_valid():
                form.save()
                messages.success(request, '项目更新成功')
                return redirect('tasks:project_detail', project_id=project.id)
            project_form = form  # In case of invalid form, show errors
        elif 'delete_project' in request.POST:
            project.delete()
            messages.success(request, '项目删除成功')
            return redirect('tasks:project_list')
        elif 'add_model' in request.POST:
            model_form = ProjectModelForm(request.POST)
            if model_form.is_valid():
                model = model_form.save(commit=False)
                model.model_belongsto_project_id = project
                model.model_creator = request.user
                model.model_created_time = timezone.now()
                model.model_updated_time = timezone.now()
                model.save()
                messages.success(request, '机型添加成功')
                return redirect('tasks:project_detail', project_id=project.id)
            else:
                messages.error(request, '添加机型失败，请检查表单信息。')
        else:
            messages.error(request, '无效的操作。')
    else:
        model_form = ProjectModelForm()
        
    context = {
        'project': project,
        'project_form': project_form,
        'model_form': model_form,
    }
    return render(request, 'tasks/project_detail.html', context)

@login_required
def model_edit(request, model_id):
    model = get_object_or_404(ProjectModel, id=model_id)
    project = model.model_belongsto_project_id
    # 检查当前用户是否为管理员或创建者
    if not (request.user == project.project_creator or request.user.is_superuser):
        messages.error(request, '您没有权限编辑该机型。')
        return redirect('tasks:project_detail', project_id=project.id)
    
    if request.method == 'POST':
        form = ProjectModelForm(request.POST, instance=model)
        if form.is_valid():
            model = form.save(commit=False)
            model.model_updated_time = timezone.now()
            model.save()
            messages.success(request, '机型更新成功')
            return redirect('tasks:project_detail', project_id=project.id)
    else:
        form = ProjectModelForm(instance=model)
    
    context = {
        'form': form,
        'title': '编辑机型',
        'model': model,
        'project': project,
    }
    
    return render(request, 'tasks/model_edit.html', context)

@login_required
def model_delete(request, model_id):
    model = get_object_or_404(ProjectModel, id=model_id)
    project = model.model_belongsto_project_id
    # 检查当前用户是否为管理员或创建者
    if not (request.user == project.project_creator or request.user.is_superuser):
        messages.error(request, '您没有权限删除该机型。')
        return redirect('tasks:project_detail', project_id=project.id)
    
    if request.method == 'POST':
        model.delete()
        messages.success(request, '机型删除成功')
        return redirect('tasks:project_detail', project_id=project.id)
    
    context = {
        'model': model,
        'project': project,
    }
    
    return render(request, 'tasks/model_confirm_delete.html', context)

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
        'projects': all_projects,
        'models': all_models,
        'status_filter': status_filter,
        'project_filter': project_filter,
        'model_filter': model_filter,
        'search_query': search_query or '',
    }

    return render(request, 'tasks/task_list.html', context)

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.task_creator = request.user
            task.save()
            messages.success(request, '任务创建成功')
            return redirect('tasks:task_list')
    else:
        form = TaskForm()
    
    context = {
        'form': form,
        'title': '创建新任务',
    }
    
    return render(request, 'tasks/task_create.html', context)

@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # 检查当前用户是否为任务创建者或负责人，或管理员
    if not (request.user == task.task_creator or request.user == task.task_assigned_to_user_id or request.user.is_superuser):
        messages.error(request, '您没有权限编辑该任务。')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, '任务更新成功')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'title': '编辑任务',
        'task': task,
    }
    
    return render(request, 'tasks/task_create.html', context)

@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # 检查当前用户是否为任务创建者或负责人，或管理员
    if not (request.user == task.task_creator or request.user == task.task_assigned_to_user_id or request.user.is_superuser):
        messages.error(request, '您没有权限删除该任务。')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, '任务删除成功')
        return redirect('tasks:task_list')
    
    context = {
        'task': task,
    }
    
    return render(request, 'tasks/task_confirm_delete.html', context)

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    commit_records = TaskCommitRecord.objects.filter(commit_belongsto_task_id=task).order_by('-commit_created_time')
    comment_records = TaskCommentRecord.objects.filter(comment_belongsto_task_id=task).order_by('comment_created_time')

    if request.method == 'POST':
        if 'add_comment' in request.POST:
            content_form = CommentForm(request.POST)
            if content_form.is_valid():
                comment = content_form.save(commit=False)                
                comment.comment_belongsto_task_id = task
                comment.comment_creator = request.user
                comment.comment_created_time = timezone.now()
                comment.comment_updated_time = timezone.now()
                comment.save()
                messages.success(request, '评论添加成功')
                return redirect('tasks:task_detail', task_id=task.id)
            else:
                messages.error(request, '评论内容不能为空。')
        elif 'add_commit' in request.POST:
            print("Received POST data for commit:", request.POST)  # Debugging line
            commit_form = CommitForm(request.POST)
            if commit_form.is_valid():
                commit = commit_form.save(commit=False)                
                commit.commit_belongsto_task_id = task
                commit.commit_created_time = timezone.now()
                commit.save()
                messages.success(request, '提交记录添加成功')
                return redirect('tasks:task_detail', task_id=task.id)
            else:
                messages.error(request, '提交记录信息有误，请检查表单。')
        elif 'update_status' in request.POST:
            new_status = request.POST.get('task_status')
            if new_status in dict(Task.STATUS_CHOICES).keys():
                task.task_status = new_status
                task.save()
                messages.success(request, '任务状态更新成功')
                return redirect('tasks:task_detail', task_id=task.id)
            else:
                messages.error(request, '无效的任务状态。')
        elif 'create_related_task' in request.POST:
            # 处理 创建关联任务的请求
            form_data = request.POST.copy()
            task_form = TaskForm(form_data)
            if task_form.is_valid():
                related_task = task_form.save(commit=False)
                related_task.task_creator = request.user
                related_task.task_source_task_id = task
                related_task.save()
                messages.success(request, '关联任务创建成功')
                return redirect('tasks:task_detail', task_id=task.id)
            else:
                messages.error(request, '关联任务信息有误，请检查表单。')
                for field, errors in task_form.errors.items():
                    for error in errors:
                        messages.error(request, f"字段 {field}: {error}")
        else:
            messages.error(request, '无效的操作。')
    else:
        content_form = CommentForm()
        commit_form = CommitForm()

    projects = Project.objects.all()
    models = ProjectModel.objects.filter(model_belongsto_project_id=task.task_belongsto_project_id)
    users = User.objects.all()

    task_types = Task.TASK_TYPE_CHOICES
    task_priorities = PRIORITY_CHOICES
    task_statuses = Task.TASK_STATUS_CHOICES

    context = {
        'task': task,
        'commit_form': commit_records,
        'comment_form': comment_records,
        'projects': projects,
        'models': models,
        'users': users,
        'task_types': task_types,
        'priorities': task_priorities,
        'statuses': task_statuses,
    }

    return render(request, 'tasks/task_detail.html', context)

@login_required
def create_related_task(request, task_id):
    source_task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            related_task = form.save(commit=False)
            related_task.task_creator = request.user
            related_task.task_source_task_id = source_task
            related_task.save()
            messages.success(request, '关联任务创建成功')
            return redirect('tasks:task_detail', task_id=source_task.id)
        else:
            messages.error(request, '关联任务信息有误，请检查表单。')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"字段 {field}: {error}")
    elif request.method == 'GET':
        initial_data = {
            'task_belongsto_project_id': source_task.task_belongsto_project_id,
            'task_belongsto_model_id': source_task.task_belongsto_model_id,
            'task_assigned_to_user_id': source_task.task_assigned_to_user_id,
            'task_type': source_task.task_type,
            'task_priority': source_task.task_priority,
        }
        form = TaskForm(initial=initial_data)
    else:
        form = TaskForm()

    projects = Project.objects.all()
    models = ProjectModel.objects.filter(model_belongsto_project_id=source_task.task_belongsto_project_id)
    users = User.objects.all()
    
    task_types = Task.TASK_TYPE_CHOICES
    task_priorities = PRIORITY_CHOICES
    task_statuses = Task.TASK_STATUS_CHOICES

    context = {
        'form': form,
        'title': '创建关联任务',
        'task': source_task,
        'projects': projects,
        'models': models,
        'users': users,
        'task_types': task_types,
        'task_priorities': task_priorities,
        'task_statuses': task_statuses,
    }

    return render(request, 'tasks/task_create.html', context)

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
def tricks_view(request):
    tricks = TrickRecord.objects.all().order_by('-trick_created_time')

    context = {
        'tricks': tricks,
    }

    return render(request, 'tasks/tricks.html', context)


@login_required
def project_models(request, project_id):
    
    try:
        models = ProjectModel.objects.filter(model_belongsto_project_id=project_id).order_by('-model_priority', '-model_created_time')
        data = [{'id': model.id, 'name': model.model_name} for model in models]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)