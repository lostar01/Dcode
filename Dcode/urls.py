"""Dcode URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.urls import path
from web.views import server,project,deploy

urlpatterns = [
    path('admin/', admin.site.urls),
    path('server/list/',server.server_list,name='server_list'),
    path('server/add/',server.server_add, name='server_add'),
    path('server/edit/<int:pk>',server.server_edit,name='server_edit'),
    path('server/del/<int:pk>',server.server_del,name='server_del'),
    path('project/list/',project.project_list,name='project_list'),
    path('project/add/',project.project_add, name='project_add'),
    path('project/edit/<int:pk>',project.project_edit,name='project_edit'),
    path('project/del/<int:pk>',project.project_del,name='project_del'),
    path('task/list/<int:project_id>',deploy.task_list,name='task_list'),
    path('task/add/<int:project_id>',deploy.task_add, name='task_add'),
    path('task/edit/<int:project_id>/<int:task_id>',deploy.task_edit, name='task_edit'),
    path('hook/template/<int:hook_id>',deploy.hook_template, name='hook_template'),

]
