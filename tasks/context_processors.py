from .models import Project

def projects_context(request):
    if request.user.is_authenticated:
        projects = Project.objects.all()[:6]  # 只取前6个项目显示在侧边栏
        return {'projects': projects}
    return {'projects': []}