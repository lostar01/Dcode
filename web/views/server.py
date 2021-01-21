from django.shortcuts import render,redirect
from django.http import JsonResponse
from web.models import Server
from django.contrib.auth.decorators import login_required
from web.views.base import BootstrapModelForm

# 为了做表单验证，引入ModelForm 的功能
#1. 自动生成表单功能
#2. 表单验证
class ServerModelForm(BootstrapModelForm):
    # exclude_bootstrap = ['notices']
    class Meta:
        model = Server
        fields = "__all__"
        # exclude = ['notices']


@login_required
def server_list(request):
    server_obj = Server.objects.all()
    return render(request,'server_list.html',locals())

@login_required
def server_add(request):
    title = "添加服务器"
    if request.method == 'GET':
        form = ServerModelForm()
    else:
        #接收用户提交的数据并进行表单验证
        form = ServerModelForm(data=request.POST)
        if form.is_valid():
            #验证通过
            form.save()
            #跳转到服务器列表页面
            return redirect('server_list')

    return render(request,'form.html',{"form": form,"title":title})

@login_required
def server_edit(request,pk):
    title = "编辑服务器"
    # server_obj = Server.objects.filter(pk=pk).first()
    server_obj = Server.objects.get(pk=pk)
    if request.method == 'GET':
        form = ServerModelForm(instance=server_obj)
    else:
        form = ServerModelForm(data=request.POST,instance=server_obj)
        if form.is_valid():
            form.save()
            return redirect('server_list')
    return render(request, 'form.html', {"form": form,"title": title})

@login_required
def server_del(request,pk):
    status = False
    if request.method == 'POST':
        try:
            Server.objects.filter(pk=pk).delete()
            status = True
        except Exception as e:
            print("删除失败")
    res = {"status": status }
    return JsonResponse(res)