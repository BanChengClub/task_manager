from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone

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
        return redirect('home')
    else:
        # 未登录，跳转到登录页面
        return redirect('login')

# BCClub: 用户注册视图
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

# BCClub: 主页视图
@login_required
def home(request):
    return