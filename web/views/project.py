from django.shortcuts import render,redirect
from django.http import JsonResponse
from web.models import Project

from django.forms import ModelForm

# 为了做表单验证，引入ModelForm 的功能
#1. 自动生成表单功能
#2. 表单验证
class ProjectModelForm(ModelForm):
    exclude_bootstrap = ['']
    class Meta:
        model = Project
        fields = "__all__"

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        #自定义功能
        for k,field in self.fields.items():
            if k in self.exclude_bootstrap:
                continue
            field.widget.attrs['class'] = 'form-control'


def project_list(request):
    project_obj = Project.objects.all()
    return render(request,'project_list.html',locals())

def project_add(request):
    if request.method == 'GET':
        form = ProjectModelForm()
    else:
        #接收用户提交的数据并进行表单验证
        form = ProjectModelForm(data=request.POST)
        if form.is_valid():
            #验证通过
            form.save()
            #跳转到服务器列表页面
            return redirect('project_list')

    return render(request,'project_add.html',{"form": form})

def project_edit(request,pk):
    # server_obj = Server.objects.filter(pk=pk).first()
    project_obj = Project.objects.get(pk=pk)
    if request.method == 'GET':
        form = ProjectModelForm(instance=project_obj)
    else:
        form = ProjectModelForm(data=request.POST,instance=project_obj)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    return render(request, 'project_edit.html', {"form": form})

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