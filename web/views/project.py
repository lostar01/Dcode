from django.shortcuts import render,redirect
from django.http import JsonResponse
from web.models import Project
from django.contrib.auth.decorators import login_required

from web.views.base import BootstrapModelForm

# 为了做表单验证，引入ModelForm 的功能
#1. 自动生成表单功能
#2. 表单验证
class ProjectModelForm(BootstrapModelForm):
    # exclude_bootstrap = ['']
    class Meta:
        model = Project
        fields = "__all__"


@login_required
def project_list(request):
    project_obj = Project.objects.all()
    return render(request,'project_list.html',locals())

@login_required
def project_add(request):
    title = "添加项目"
    if request.method == 'GET':
        form = ProjectModelForm()
    else:
        #接收用户提交的数据并进行表单验证
        print(request.POST)
        form = ProjectModelForm(data=request.POST)
        if form.is_valid():
            #验证通过
            form.save()
            #跳转到服务器列表页面
            return redirect('project_list')

    return render(request,'form.html',{"form": form,"title": title})

@login_required
def project_edit(request,pk):
    title = "编辑项目"
    # server_obj = Server.objects.filter(pk=pk).first()
    project_obj = Project.objects.get(pk=pk)
    if request.method == 'GET':
        form = ProjectModelForm(instance=project_obj)
    else:
        print(request.POST)
        form = ProjectModelForm(data=request.POST,instance=project_obj)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    return render(request, 'form.html', {"form": form,"title": title})

@login_required
def project_del(request,pk):
    status = False
    if request.method == 'POST':
        try:
            Project.objects.filter(pk=pk).delete()
            status = True
        except Exception as e:
            print("删除失败")
    res = {"status": status }
    return JsonResponse(res)

def loading(request):
    return render(request,'loading.html')