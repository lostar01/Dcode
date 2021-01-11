from django.shortcuts import render,reverse,redirect
from web.models import DeployTask,Project
from web.views.base import BootstrapModelForm
import uuid


class DeplayTaskModelForm(BootstrapModelForm):

    class Meta:
        model = DeployTask
        fields = "__all__"
        exclude = ["uuid","project","status"]

    # def save(self, commit=True):


def task_list(request,project_id):
    task_obj = DeployTask.objects.filter(project_id=project_id).all()
    probj = Project.objects.get(pk=project_id)
    title = "发布单任务单:" + probj.title + " " + probj.get_env_display()
    return render(request,'task_list.html',{"task_obj": task_obj,"title": title,"probj": probj })


def task_add(request,project_id):
    probj = Project.objects.get(pk=project_id)
    title = "添加发布单任务单:" + probj.title + " " + probj.get_env_display()

    if request.method == 'GET':
        form = DeplayTaskModelForm()
    else:
        data = request.POST
        form = DeplayTaskModelForm(data=data)
        if form.is_valid():
            tdobj = DeployTask()
            tdobj.project = probj
            tdobj.uuid = (str(uuid.uuid4()) + str(uuid.uuid4())).replace('-',"")[:32]
            tdobj.tag = data.get('tag')
            tdobj.before_download_script = data.get("before_download_script")
            tdobj.after_download_script = data.get("after_download_script")
            tdobj.before_deploy_script = data.get("before_deploy_script")
            tdobj.after_deploy_script = data.get("after_deploy_script")
            try:
                tdobj.save()
            except Exception as e:
                print(e)
            url = reverse('task_list',kwargs={"project_id": project_id })

            return redirect(url)

    return render(request,"task_form.html",{"form": form,"title":title ,"probj": probj})

def task_edit(request,project_id,task_id):
    task_obj = DeployTask.objects.get(pk=task_id)
    if request.method == 'GET':
        form = DeplayTaskModelForm(instance=task_obj)
    else:
        data = request.POST
        form = DeplayTaskModelForm(request.POST)
        if form.is_valid():
            task_obj.tag = data.get('tag')
            task_obj.before_download_script = data.get("before_download_script")
            task_obj.after_download_script = data.get("after_download_script")
            task_obj.before_deploy_script = data.get("before_deploy_script")
            task_obj.after_deploy_script = data.get("after_deploy_script")
            try:
                task_obj.save()
            except Exception as e:
                print(e)
            url = reverse('task_list', kwargs={"project_id": project_id})
            return redirect(url)


    return render(request,"form.html",{"form": form })