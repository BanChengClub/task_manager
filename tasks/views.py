from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Task, Project, ProductModel, Commit, Comment, Knowledge
from .forms import TaskForm, CommitForm, CommentForm, ProjectForm, ProductModelForm
from django.contrib import messages
from django.http import JsonResponse
from .models import ProductModel


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
    # 合并所有筛选条件
    status_filter = request.GET.get('status')
    project_filter = request.GET.get('project')
    search_query = request.GET.get('q')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)
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

    # 初始化表单变量
    comment_form = CommentForm()
    commit_form = CommitForm()

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
        elif 'create_related_task' in request.POST:
            # 处理创建关联任务的请求
            # 创建一个TaskForm实例来处理数据
            form_data = request.POST.copy()
            # 确保源任务字段正确设置
            form_data['source_task'] = task.id

            form = TaskForm(form_data)
            if form.is_valid():
                new_task = form.save(commit=False)
                new_task.created_by = request.user
                new_task.save()
                messages.success(request, '关联任务已创建')
                return redirect('tasks:task_detail', task_id=new_task.id)
            else:
                # 如果表单验证失败，显示错误信息
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        comment_form = CommentForm()
        commit_form = CommitForm()

    # 准备关联任务模态框所需的数据
    projects = Project.objects.all()
    # 获取当前任务项目的机型
    models = ProductModel.objects.filter(project=task.project)
    users = User.objects.all()

    # 获取任务类型和优先级的选项
    task_types = Task.TASK_TYPE_CHOICES
    priorities = Task.PRIORITY_CHOICES

    context = {
        'task': task,
        'comment_form': comment_form,
        'commit_form': commit_form,
        'projects': projects,
        'models': models,
        'users': users,
        'task_types': task_types,
        'priorities': priorities,
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
    # 获取请求的年份和月份，默认为当前
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    # 计算当月第一天和最后一天
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year, month, 31).date()
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)

    # 筛选当月任务
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

    # 传递月份导航参数
    context = {
        'tasks_by_date': tasks_by_date,
        'first_day': first_day,
        'current_year': year,
        'current_month': month,
        'prev_year': year if month > 1 else year - 1,
        'prev_month': month - 1 if month > 1 else 12,
        'next_year': year if month < 12 else year + 1,
        'next_month': month + 1 if month < 12 else 1,
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
def create_related_task(request, task_id):
    # 获取源任务
    source_task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        # 创建新任务表单实例，包含POST数据
        form = TaskForm(request.POST)

        if form.is_valid():
            # 保存新任务
            new_task = form.save(commit=False)
            new_task.created_by = request.user
            new_task.save()

            # 重定向到新创建的任务详情页面
            return redirect('tasks:task_detail', task_id=new_task.id)
    else:
        # 如果是GET请求，预填充一些字段
        initial_data = {
            'project': source_task.project,
            'model': source_task.model,
            'source_task': source_task,
        }
        form = TaskForm(initial=initial_data)

    # 准备模态框所需的数据
    projects = Project.objects.all()
    models = ProductModel.objects.all()
    users = User.objects.all()

    # 获取任务类型和优先级的选项
    task_types = Task.TASK_TYPE_CHOICES
    priorities = Task.PRIORITY_CHOICES

    context = {
        'source_task': source_task,
        'form': form,
        'projects': projects,
        'models': models,
        'users': users,
        'task_types': task_types,
        'priorities': priorities,
    }

    return render(request, 'tasks/create_related_task.html', context)

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

@login_required
def get_models_by_project(request, project_id):
    """根据项目ID返回对应的机型列表"""
    try:
        models = ProductModel.objects.filter(project_id=project_id)
        data = [{"id": m.id, "name": m.name} for m in models]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)