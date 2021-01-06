from django.shortcuts import render,redirect
from django.http import JsonResponse
from web.models import Server

from django.forms import ModelForm

# 为了做表单验证，引入ModelForm 的功能
#1. 自动生成表单功能
#2. 表单验证
class ServerModelForm(ModelForm):
    exclude_bootstrap = ['']
    class Meta:
        model = Server
        fields = "__all__"

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        #自定义功能
        for k,field in self.fields.items():
            if k in self.exclude_bootstrap:
                continue
            field.widget.attrs['class'] = 'form-control'


def server_list(request):
    server_obj = Server.objects.all()
    return render(request,'server_list.html',locals())

def server_add(request):
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

    return render(request,'server_add.html',{"form": form})

def server_edit(request,pk):
    # server_obj = Server.objects.filter(pk=pk).first()
    server_obj = Server.objects.get(pk=pk)
    if request.method == 'GET':
        form = ServerModelForm(instance=server_obj)
    else:
        form = ServerModelForm(data=request.POST,instance=server_obj)
        if form.is_valid():
            form.save()
            return redirect('server_list')
    return render(request, 'server_edit.html', {"form": form})

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