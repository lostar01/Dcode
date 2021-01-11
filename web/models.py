from django.db import models

# Create your models here.

class Server(models.Model):
    """
    服务器表
    """
    hostname = models.CharField(verbose_name='主机名',max_length=32)
    notices = models.CharField(verbose_name='备注',max_length=32,blank=True,default="")

    def __str__(self):
        return self.hostname


class Project(models.Model):
    title = models.CharField(verbose_name="项目名", max_length=32)

    #https://www.github.com/xxx.git
    repo = models.CharField(verbose_name="仓库地址", max_length=128)

    env_choice = (
        ('prod','正式'),
        ('test','测试')
    )
    env = models.CharField(verbose_name="环境", max_length=16,choices=env_choice,default="test")
    path = models.CharField(verbose_name="线上路径",max_length=64,default="")
    server = models.ManyToManyField(verbose_name="关联服务器",to='Server')
    def __str__(self):
        return self.title


class DeployTask(models.Model):
    uuid = models.CharField(verbose_name='标识',max_length=64)
    project = models.ForeignKey(verbose_name="项目环境",to='Project',on_delete=models.CASCADE)
    tag = models.CharField(verbose_name="版本",max_length=32)

    status_choices = (
        (1,'待发布'),
        (2,'发布中'),
        (3,'成功'),
        (4,'失败'),
    )

    status = models.SmallIntegerField(verbose_name="状态",choices=status_choices,default=1)
    before_download_script = models.TextField(verbose_name="下载前脚本",null=True,blank=True)
    after_download_script = models.TextField(verbose_name="下载后脚本",null=True,blank=True)
    before_deploy_script = models.TextField(verbose_name="发布前脚本",null=True,blank=True)
    after_deploy_script = models.TextField(verbose_name="发布后脚本",null=True,blank=True)


class HookTemplate(models.Model):
    """
    钩子模板
    """
    title = models.CharField(verbose_name="标题",max_length=32)
    content = models.TextField(verbose_name="脚本内容")
    hook_choice = (
        (2,'下载前'),
        (4,'下载后'),
        (6,'发布前'),
        (8,'发布后')
    )
    hook_type = models.SmallIntegerField(verbose_name="钩子类型",choices=hook_choice)