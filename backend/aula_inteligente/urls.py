"""
URL configuration for aula_inteligente project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.contrib.auth import get_user_model

def check_superuser(request):
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if user:
        return JsonResponse({
            "username": user.username,
            "email": user.email
        })
    return JsonResponse({"error": "No superuser found"}, status=404)

def home(request):
    return JsonResponse({"status": "ok", "message": "Django está vivo 🚀"})

urlpatterns = [
    path('', home),  # <- ESTA es la clave para mostrar algo en "/"
    path('admin/', admin.site.urls),
    path('check-superuser/', check_superuser),  # ⬅️ TEMPORAL
    path('api/usuarios/', include('apps.usuarios.urls')),
    path('api/materias/', include('apps.materias.urls')),
    path('api/notas/', include('apps.notas.urls')),
    path('api/asistencias/', include('apps.asistencias.urls')),
    path('api/participaciones/', include('apps.participaciones.urls')),
    path('api/predicciones/', include('apps.predicciones.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/cursos/', include('apps.cursos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
]
