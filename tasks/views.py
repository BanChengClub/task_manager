from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Task, Project, ProductModel, Commit, Comment, Knowledge
from .forms import TaskForm, CommitForm, CommentForm, ProjectForm, ProductModelForm
from django.contrib import messages


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('tasks:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})


@login_required
def dashboard(request):
    # 获取统计信息
    total_tasks = Task.objects.filter(assigned_to=request.user).count()
    pending_tasks = Task.objects.filter(assigned_to=request.user, status='pending').count()
    in_progress_tasks = Task.objects.filter(assigned_to=request.user, status='in-progress').count()
    completed_tasks = Task.objects.filter(assigned_to=request.user, status='completed').count()

    # 获取今天到期的任务
    today = timezone.now().date()
    today_tasks = Task.objects.filter(
        assigned_to=request.user,
        due_date=today,
        status__in=['pending', 'in-progress']
    )

    # 获取最近任务
    recent_tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')[:10]

    # 获取即将到期的任务
    due_soon_tasks = Task.objects.filter(
        assigned_to=request.user,
        due_date__gte=today,
        due_date__lte=today + timedelta(days=7),
        status__in=['pending', 'in-progress']
    )

    # 获取项目统计
    projects = Project.objects.annotate(
        task_count=Count('tasks', filter=Q(tasks__assigned_to=request.user)),
        completed_count=Count('tasks', filter=Q(tasks__assigned_to=request.user, tasks__status='completed'))
    )

    # 获取所有项目用于侧边栏
    all_projects = Project.objects.all()[:6]  # 只取前6个项目显示在侧边栏

    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'today_tasks': today_tasks,
        'recent_tasks': recent_tasks,
        'due_soon_tasks': due_soon_tasks,
        'projects': projects,
        'all_projects': all_projects,  # 传递给侧边栏
    }

    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user)

    # 处理筛选
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # 处理项目筛选
    project_filter = request.GET.get('project')
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)

    # 处理搜索
    search_query = request.GET.get('q')
    if search_query:
        tasks = tasks.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    # 获取所有项目用于筛选
    projects = Project.objects.all()

    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'project_filter': project_filter,
        'search_query': search_query or '',
        'projects': projects,
    }

    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    if request.method == 'POST':
        if 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.task = task
                comment.author = request.user
                comment.save()
                messages.success(request, '评论已添加')
                return redirect('tasks:task_detail', task_id=task.id)
        elif 'add_commit' in request.POST:
            commit_form = CommitForm(request.POST)
            if commit_form.is_valid():
                commit = commit_form.save(commit=False)
                commit.task = task
                commit.save()
                messages.success(request, '提交记录已添加')
                return redirect('tasks:task_detail', task_id=task.id)
        elif 'update_status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in dict(Task.STATUS_CHOICES).keys():
                task.status = new_status
                task.save()
                messages.success(request, '任务状态已更新')
                return redirect('tasks:task_detail', task_id=task.id)
    else:
        comment_form = CommentForm()
        commit_form = CommitForm()

    context = {
        'task': task,
        'comment_form': comment_form,
        'commit_form': commit_form,
    }

    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            if not task.assigned_to:
                task.assigned_to = request.user
            task.save()
            messages.success(request, '任务创建成功')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        # 设置默认值为当前用户
        form = TaskForm(initial={'assigned_to': request.user})

    context = {
        'form': form,
        'title': '创建新任务',
    }

    return render(request, 'tasks/task_form.html', context)


@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by=request.user)

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

    return render(request, 'tasks/task_form.html', context)


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by=request.user)

    if request.method == 'POST':
        try:
            task.delete()
            messages.success(request, '任务已删除')
            return redirect('tasks:dashboard')
        except Exception as e:
            messages.error(request, f'删除任务时出错: {str(e)}')
            return redirect('tasks:task_detail', task_id=task.id)

    context = {
        'task': task,
    }

    return render(request, 'tasks/task_confirm_delete.html', context)


@login_required
def calendar_view(request):
    # 获取当前月的任务
    today = timezone.now().date()
    first_day = today.replace(day=1)

    # 计算最后一天
    if first_day.month == 12:
        last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)

    tasks = Task.objects.filter(
        assigned_to=request.user,
        due_date__gte=first_day,
        due_date__lte=last_day
    )

    # 按日期组织任务
    tasks_by_date = {}
    for task in tasks:
        if task.due_date not in tasks_by_date:
            tasks_by_date[task.due_date] = []
        tasks_by_date[task.due_date].append(task)

    context = {
        'tasks_by_date': tasks_by_date,
        'first_day': first_day,
        'last_day': last_day,
        'today': today,
    }

    return render(request, 'tasks/calendar.html', context)


@login_required
def knowledge_base(request):
    knowledge_items = Knowledge.objects.all()

    context = {
        'knowledge_items': knowledge_items,
    }

    return render(request, 'tasks/knowledge.html', context)


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
def model_list(request):
    models = ProductModel.objects.all()

    if request.method == 'POST':
        form = ProductModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '机型创建成功')
            return redirect('tasks:model_list')
    else:
        form = ProductModelForm()

    context = {
        'models': models,
        'form': form,
    }

    return render(request, 'tasks/model_list.html', context)


from django.shortcuts import render


@login_required
def project_list(request):
    projects = Project.objects.all()

    context = {
        'projects': projects,
    }

    return render(request, 'tasks/project_list.html', context)


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        if 'add_model' in request.POST:
            model_form = ProductModelForm(request.POST)
            if model_form.is_valid():
                model = model_form.save(commit=False)
                model.project = project  # 确保项目被正确设置
                model.save()
                messages.success(request, '机型添加成功')
                return redirect('tasks:project_detail', project_id=project.id)
            else:
                # 添加错误信息显示
                messages.error(request, '机型添加失败，请检查表单')
        elif 'edit_project' in request.POST:
            project_form = ProjectForm(request.POST, instance=project)
            if project_form.is_valid():
                project_form.save()
                messages.success(request, '项目更新成功')
                return redirect('tasks:project_detail', project_id=project.id)
    else:
        model_form = ProductModelForm()
        project_form = ProjectForm(instance=project)

    context = {
        'project': project,
        'model_form': model_form,
        'project_form': project_form,
    }

    return render(request, 'tasks/project_detail.html', context)


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, '项目创建成功')
            return redirect('tasks:project_detail', project_id=project.id)
    else:
        form = ProjectForm()

    context = {
        'form': form,
        'title': '创建新项目',
    }

    return render(request, 'tasks/project_form.html', context)


@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id, created_by=request.user)

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

    return render(request, 'tasks/project_form.html', context)


@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id, created_by=request.user)

    if request.method == 'POST':
        project.delete()
        messages.success(request, '项目已删除')
        return redirect('tasks:project_list')

    context = {
        'project': project,
    }

    return render(request, 'tasks/project_confirm_delete.html', context)


@login_required
def model_edit(request, model_id):
    model = get_object_or_404(ProductModel, id=model_id)

    if request.method == 'POST':
        form = ProductModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            messages.success(request, '机型更新成功')
            return redirect('tasks:project_detail', project_id=model.project.id)
    else:
        form = ProductModelForm(instance=model)

    context = {
        'form': form,
        'title': '编辑机型',
        'model': model,
    }

    return render(request, 'tasks/model_form.html', context)


@login_required
def model_delete(request, model_id):
    model = get_object_or_404(ProductModel, id=model_id)
    project_id = model.project.id

    if request.method == 'POST':
        model.delete()
        messages.success(request, '机型已删除')
        return redirect('tasks:project_detail', project_id=project_id)

    context = {
        'model': model,
    }

    return render(request, 'tasks/model_confirm_delete.html', context)


from django.http import JsonResponse


@login_required
def project_models_api(request, project_id):
    """获取指定项目的机型列表（API）"""
    try:
        project = Project.objects.get(id=project_id)
        models = project.models.all()  # 使用related_name

        data = [
            {
                'id': model.id,
                'name': model.name,
                'description': model.description
            }
            for model in models
        ]

        return JsonResponse(data, safe=False)

    except Project.DoesNotExist:
        return JsonResponse({'error': '项目不存在'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def debug_info(request):
    """显示调试信息"""
    info = {
        'user': str(request.user),
        'projects_count': Project.objects.count(),
        'models_count': ProductModel.objects.count(),
        'tasks_count': Task.objects.count(),
        'projects': list(Project.objects.values('id', 'name', 'created_by')),
        'models': list(ProductModel.objects.values('id', 'name', 'project')),
        'tasks': list(Task.objects.values('id', 'title', 'project', 'model', 'created_by')),
    }

    return JsonResponse(info)