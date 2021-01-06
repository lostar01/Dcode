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