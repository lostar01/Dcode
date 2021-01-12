import datetime
from django.shortcuts import render,reverse,redirect
from web.models import DeployTask,Project,HookTemplate
from web.views.base import BootstrapModelForm
from django import forms
from django.http import JsonResponse
import uuid


class DeplayTaskModelForm(BootstrapModelForm):
    exclude_bootstrap = ["before_download_template","after_download_template","before_deploy_template","after_deploy_template"]

    before_download_select = forms.ChoiceField(required=False, label="下载前")
    before_download_title = forms.CharField(required=False,label="模板名称")
    before_download_template = forms.BooleanField(required=False,widget=forms.CheckboxInput,label="是否保存模板")

    after_download_select = forms.ChoiceField(required=False, label="下载后")
    after_download_title = forms.CharField(required=False, label="模板名称")
    after_download_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label="是否保存模板")

    before_deploy_select = forms.ChoiceField(required=False, label="发布前")
    before_deploy_title = forms.CharField(required=False, label="模板名称")
    before_deploy_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label="是否保存模板")

    after_deploy_select = forms.ChoiceField(required=False, label="发布后")
    after_deploy_title = forms.CharField(required=False, label="模板名称")
    after_deploy_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label="是否保存模板")

    class Meta:
        model = DeployTask
        fields = "__all__"
        exclude = ["uuid","project","status"]

    def __init__(self,project_obj,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.project_obj = project_obj

        self.init_hook()

    def init_hook(self):
        before_download = [(0,'请选择')]
        before_download.extend(HookTemplate.objects.filter(hook_type=2).values_list('id','title'))
        after_download = [(0, '请选择')]
        after_download.extend(HookTemplate.objects.filter(hook_type=4).values_list('id','title'))
        before_deploy = [(0, '请选择')]
        before_deploy.extend(HookTemplate.objects.filter(hook_type=6).values_list('id','title'))
        after_deploy = [(0, '请选择')]
        after_deploy.extend(HookTemplate.objects.filter(hook_type=8).values_list('id','title'))

        self.fields["before_download_select"].choices=before_download
        self.fields["after_download_select"].choices=after_download
        self.fields["before_deploy_select"].choices=before_deploy
        self.fields["after_deploy_select"].choices=after_deploy

    def save(self, commit=True):
        self.instance.uuid = self.create_uid()
        self.instance.project_id = self.project_obj.id
        super(DeplayTaskModelForm, self).save(commit)

        #模板钩子
        if self.cleaned_data.get('before_download_template'):
            title = self.cleaned_data.get('before_download_title')
            content = self.cleaned_data.get('before_download_script')
            HookTemplate.objects.create(title=title,content=content,hook_type=2)

        if self.cleaned_data.get('after_download_template'):
            title = self.cleaned_data.get('after_download_title')
            content = self.cleaned_data.get('after_download_script')
            HookTemplate.objects.create(title=title,content=content,hook_type=4)

        if self.cleaned_data.get('before_deploy_template'):
            title = self.cleaned_data.get('before_deploy_title')
            content = self.cleaned_data.get('before_deploy_script')
            HookTemplate.objects.create(title=title,content=content,hook_type=6)

        if self.cleaned_data.get('after_deploy_template'):
            title = self.cleaned_data.get('after_deploy_title')
            content = self.cleaned_data.get('after_deploy_script')
            HookTemplate.objects.create(title=title,content=content,hook_type=8)


    def create_uid(self):
        title = self.project_obj.title
        env = self.project_obj.env
        tag = self.cleaned_data.get("tag")
        date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        return "{0}-{1}-{2}-{3}".format(title,env,tag,date)

    def clean(self):
        if self.cleaned_data.get('before_download_template'):
            title = self.cleaned_data.get('before_download_title')
            if not title:
                self.add_error("before_download_title","请输入模板名称")
                # raise ValidationError('请输入模板名称')
        # return self.cleaned_data

        if self.cleaned_data.get('after_download_template'):
            title = self.cleaned_data.get('after_download_title')
            if not title:
                self.add_error("after_download_title","请输入模板名称")

        if self.cleaned_data.get('before_deploy_template'):
            title = self.cleaned_data.get('before_deploy_title')
            if not title:
                self.add_error("before_deploy_title","请输入模板名称")
                # raise ValidationError('请输入模板名称')
        # return self.cleaned_data

        if self.cleaned_data.get('after_deploy_template'):
            title = self.cleaned_data.get('after_deploy_title')
            if not title:
                self.add_error("after_deploy_title","请输入模板名称")




def task_list(request,project_id):
    task_obj = DeployTask.objects.filter(project_id=project_id).all()
    probj = Project.objects.get(pk=project_id)
    title = "发布单任务单:" + probj.title + " " + probj.get_env_display()
    return render(request,'task_list.html',{"task_obj": task_obj,"title": title,"probj": probj })


def task_add(request,project_id):
    probj = Project.objects.get(pk=project_id)
    title = "添加发布单任务单:" + probj.title + " " + probj.get_env_display()

    if request.method == 'GET':
        form = DeplayTaskModelForm(probj)
    else:
        data = request.POST
        form = DeplayTaskModelForm(probj,data=data)
        if form.is_valid():
            # tdobj = DeployTask()
            # tdobj.project = probj
            # tdobj.uuid = (str(uuid.uuid4()) + str(uuid.uuid4())).replace('-',"")[:32]
            # tdobj.tag = data.get('tag')
            # tdobj.before_download_script = data.get("before_download_script")
            # tdobj.after_download_script = data.get("after_download_script")
            # tdobj.before_deploy_script = data.get("before_deploy_script")
            # tdobj.after_deploy_script = data.get("after_deploy_script")
            # try:
            #     tdobj.save()
            # except Exception as e:
            #     print(e)
            form.save()
            url = reverse('task_list',kwargs={"project_id": project_id })

            return redirect(url)


    return render(request,"task_form.html",{"form": form,"title":title ,"probj": probj})

def task_edit(request,project_id,task_id):
    task_obj = DeployTask.objects.get(pk=task_id)
    probj = Project.objects.get(pk=project_id)
    title = "编辑{0}".format(task_obj.uuid)
    if request.method == 'GET':
        form = DeplayTaskModelForm(probj,instance=task_obj)
    else:
        data = request.POST
        form = DeplayTaskModelForm(probj,instance=task_obj,data=data)
        if form.is_valid():
            # task_obj.tag = data.get('tag')
            # task_obj.before_download_script = data.get("before_download_script")
            # task_obj.after_download_script = data.get("after_download_script")
            # task_obj.before_deploy_script = data.get("before_deploy_script")
            # task_obj.after_deploy_script = data.get("after_deploy_script")
            # try:
            #     task_obj.save()
            # except Exception as e:
            #     print(e)
            form.save()
            url = reverse('task_list', kwargs={"project_id": project_id})
            return redirect(url)


    return render(request,"task_form.html",{"form": form,"title":title ,"probj": probj})

def task_del(request,task_id):
    status = False
    if request.method == 'POST':
        try:
            DeployTask.objects.filter(pk=task_id).delete()
            status = True
        except Exception as e:
            print("删除失败")
    res = {"status": status}
    return JsonResponse(res)

def hook_template(request,hook_id):
    # hook_obj = HookTemplate.objects.filter(pk=hook_id).first()
    hook_obj = HookTemplate.objects.get(pk=hook_id)

    return JsonResponse({'status':True,'content': hook_obj.content})

def deploy_task(request,task_id):
    task_obj = DeployTask.objects.get(pk=task_id)
    title = "发布{0}".format(task_obj.uuid)

    return render(request,'deploy.html',{"task_obj": task_obj,"title": title})