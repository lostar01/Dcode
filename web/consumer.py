import json
import os
import subprocess
import time
from threading import Thread

import paramiko
from channels.generic.websocket import WebsocketConsumer, StopConsumer
from asgiref.sync import async_to_sync
from git import Repo

from Dcode.settings import DEPLOY_DIR, SSH_KEY, OPS_USER, SERVER_PORT
from web.models import Node, DeployTask


class DeployConsumer(WebsocketConsumer):

    def websocket_connect(self, message):
        self.accept()
        self.task_id = self.scope['url_route']['kwargs'].get('task_id')  # session 参数 cookie 等大字典
        print(self.task_id)
        async_to_sync(self.channel_layer.group_add)(self.task_id, self.channel_name)

        # task_obj = DeployTask.objects.get(pk=self.task_id)
        # if task_obj.status == 3 or task_obj.status == 4:
        #     node_qs = Node.objects.filter(task_id=self.task_id)
        #     node_list = []
        #     for row in node_qs:
        #         node_list.append(row)
        #     self.send_node_data(node_list)

    def websocket_receive(self, message):
        task_obj = DeployTask.objects.get(pk=self.task_id)
        txt = message['text']
        if txt == 'init':
            # 创建节点的列表
            node_obj_list = []
            """
            node_list = [
                {"key": "start", "text": '开始', "figure": 'Ellipse', "color": "lightgreen"},
                {"key": "download", "parent": 'start', "text": '下载代码', "color": "lightgreen", "link_text": '执行中...'},
                {"key": "compile", "parent": 'download', "text": '本地编译', "color": "lightgreen"},
                {"key": "zip", "parent": 'compile', "text": '打包', "color": "red", "link_color": 'red'},
                {"key": "c1", "text": '服务器1', "parent": "zip"},
                {"key": "c11", "text": '服务重启', "parent": "c1"},
                {"key": "c2", "text": '服务器2', "parent": "zip"},
                {"key": "c21", "text": '服务重启', "parent": "c2"},
                {"key": "c3", "text": '服务器3', "parent": "zip"},
                {"key": "c31", "text": '服务重启', "parent": "c3"} 
                ] 
            """
            # self.send(text_data=json.dumps({'code': 'init','data': node_list}))
            # 判断task 是否完成如果，完成不再初始化，否则，重新初始化节点，并返回

            node_qs = Node.objects.filter(task_id=self.task_id)

            if not node_qs:

                start_node = Node.objects.create(text='开始', task_id=self.task_id)

                if task_obj.before_download_script:
                    before_download_node = Node.objects.create(text='下载前', task_id=self.task_id, parent=start_node)
                    download_node = Node.objects.create(text='下载', task_id=self.task_id, parent=before_download_node)
                    node_obj_list.append(before_download_node)
                else:
                    download_node = Node.objects.create(text='下载', task_id=self.task_id, parent=start_node)

                if task_obj.after_download_script:
                    after_download_node = Node.objects.create(text='下载后', task_id=self.task_id, parent=download_node)
                    upload_node = Node.objects.create(text='上传', task_id=self.task_id, parent=after_download_node)
                    node_obj_list.append(after_download_node)
                else:
                    upload_node = Node.objects.create(text='上传', task_id=self.task_id, parent=download_node)

                node_obj_list.extend([start_node, download_node, upload_node])

                for server in task_obj.project.server.all():
                    row = Node.objects.create(text=server.hostname,
                                              task_id=self.task_id,
                                              parent=upload_node,
                                              server=server)
                    node_obj_list.append(row)
                    if task_obj.before_deploy_script:
                        before_deploy_node = Node.objects.create(text='发布前', server_id=server.id, task_id=self.task_id,
                                                                 parent=row)
                        node_obj_list.append(before_deploy_node)

                    if task_obj.after_deploy_script:
                        after_deploy_node = Node.objects.create(text='发布后', server_id=server.id, task_id=self.task_id,
                                                                parent=before_deploy_node)
                        node_obj_list.append(after_deploy_node)




            else:
                for row in node_qs:
                    node_obj_list.append(row)

            self.send_node_data(node_obj_list)



        elif txt == 'deploy':
            t1 = Thread(target=self.deploy, args=(task_obj,))
            t1.start()

    def send_node_data(self, node_obj_list):
        node_list = []
        # print(node_obj_list)

        for node_obj in node_obj_list:
            temp = {
                "key": str(node_obj.id),
                "text": str(node_obj.text),
                "link_color": str(node_obj.status),
                "color": str(node_obj.status),
            }

            if node_obj.parent:
                temp["parent"] = str(node_obj.parent_id)
            node_list.append(temp)

        # print(node_list,"----")

        data = json.dumps({'code': 'init', 'data': node_list})
        async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})

    def node_save(self, node_obj, status):
        try:
            node_obj.status = status
            node_obj.save()
        except:
            print("发布任务单: %s %s 修改状态失败" % (self.task_id, node_obj.text))

    def deploy(self, task_obj):
        project_dir = os.path.join(DEPLOY_DIR, task_obj.uuid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        script_dir = os.path.join(project_dir, "scripts")
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        release_dir = os.path.join(project_dir,"release")
        if not os.path.exists(release_dir):
            os.makedirs(release_dir)
        self.send_deploy_data("[开始]====>")
        start_node = Node.objects.filter(text="开始", task_id=self.task_id).first()
        self.node_save(start_node, "green")
        # data = json.dumps({'code': 'update', 'node_id': start_node.id, 'status': 'green'})
        # async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})
        self.update_node_status(start_node.id, "green")

        if task_obj.before_download_script:
            # To do
            result = True
            self.send_deploy_data("[下载前]==>")
            # self.do_before_download_script(project_dir,script_dir)
            if "bash" in task_obj.before_download_script[:40]:
                s_file = os.path.join(script_dir, "before_download_script.sh")
                with open(s_file, "w") as f:
                    f.write(task_obj.before_download_script)
                try:
                    subprocess.Popen("dos2unix %s" % (s_file),
                                     shell=True)
                    time.sleep(0.1)
                    before_download_script_rs = subprocess.Popen(
                        "bash {0}".format(s_file), shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.send_deploy_data(before_download_script_rs.stdout.read().decode())
                    self.send_deploy_data(before_download_script_rs.stderr.read().decode())
                except:
                    self.send_deploy_data("dos2unix command maybe not install,pls check.")
                    result = False
            elif "python" in task_obj.before_download_script[:40]:
                s_file = os.path.join(script_dir, "before_download_script.py")
                with open(s_file, "w") as f:
                    f.write(task_obj.before_download_script)
                try:
                    subprocess.Popen("dos2unix %s" % (s_file),
                                     shell=True)

                    before_download_script_rs = subprocess.Popen("chmod a+x {0};{1}".format(s_file,s_file),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    self.send_deploy_data(before_download_script_rs.stdout.read().decode())
                    self.send_deploy_data(before_download_script_rs.stdout.read().decode())
                except:
                    self.send_deploy_data("dos2unix command maybe not install,pls check.")
                    result = False

            else:
                self.send_deploy_data("task_obj_id: %s before_download_script format not correct." % (task_obj.id))
                result = False


            # 改变"下载前"node状态
            before_download_node = Node.objects.filter(text='下载前', task_id=self.task_id).first()
            if result:
                self.node_save(before_download_node, "green")
                self.update_node_status(before_download_node.id, "green")
            else:
                self.node_save(before_download_node, "red")
                self.update_node_status(before_download_node.id, "red")
                return

        # 改变"下载"node状态
        result = True
        self.send_deploy_data("[下载]====>")
        try:
            print(task_obj.project.repo,task_obj.tag)
            Repo.clone_from(task_obj.project.repo, to_path=os.path.join(project_dir,task_obj.project.title), branch=task_obj.tag)
        except:
            result = False
            self.send_deploy_data("下载代码出错,请检查目录是否不为空，或网络是否正常")

        download_node = Node.objects.filter(text='下载', task_id=self.task_id).first()
        if result:
            self.node_save(download_node, "green")
            self.update_node_status(download_node.id, "green")
        else:
            self.node_save(download_node, "red")
            self.update_node_status(download_node.id, "red")
            return

        #下载后
        if task_obj.after_download_script:
            # To do
            result = True
            self.send_deploy_data("[下载后]==>")
            # self.do_after_download_script()
            if "bash" in task_obj.after_download_script[:40]:
                s_file = os.path.join(script_dir,"after_download_script.sh")
                try:
                    with open(s_file,"w") as f:
                        f.write(task_obj.after_download_script)
                    subprocess.Popen("dos2unix {0}".format(s_file),shell=True)
                    time.sleep(0.1)
                    rs_after_download_script = subprocess.Popen("bash {0}".format(s_file),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=project_dir)
                    self.send_deploy_data(rs_after_download_script.stdout.read().decode())
                    self.send_deploy_data(rs_after_download_script.stderr.read().decode())
                except:
                    result = False
                    self.send_deploy_data("请检查命令dos2unix  或者文件after_download_script.sh是否正常!")
            elif "python" in task_obj.after_download_script[:40]:
                s_file = os.path.join(script_dir, "after_download_script.py")
                try:
                    with open(s_file, "w") as f:
                        f.write(task_obj.after_download_script)
                    subprocess.Popen("dos2unix {0}".format(s_file), shell=True)
                    time.sleep(0.1)
                    rs_after_download_script = subprocess.Popen("chmod a+x {0};{1}".format(s_file,s_file), stdout=subprocess.PIPE,
                                                                stderr=subprocess.PIPE, cwd=project_dir)
                    self.send_deploy_data(rs_after_download_script.stdout.read().decode())
                    self.send_deploy_data(rs_after_download_script.stderr.read().decode())
                except:
                    result = False
                    self.send_deploy_data("请检查命令dos2unix  或者文件after_download_script.py是否正常!")
            else:
                result = False
                self.send_deploy_data("脚本格式不正确，请在首行声明解析器")
            # 改变"下载后"node状态
            after_download_node = Node.objects.filter(text='下载后', task_id=self.task_id).first()
            if result:
                self.node_save(after_download_node, "green")
                self.update_node_status(after_download_node.id, "green")
            else:
                self.node_save(after_download_node, "red")
                self.update_node_status(after_download_node.id, "red")
                return

        #上传
        result = True
        self.send_deploy_data("[上传]====>")
        try:
            tar_cmd = "tar -czf release-{0}.tar.gz {1}".format(task_obj.project.title, release_dir)
            subprocess.Popen(tar_cmd,shell=True)
        except:
            self.send_deploy_data("打包release 文件失败，请检查！")
            result = False
        upload_node = Node.objects.filter(text='上传', task_id=self.task_id).first()
        if result:
            self.node_save(upload_node, "green")
            self.update_node_status(upload_node.id, "green")
        else:
            self.node_save(upload_node, "red")
            self.update_node_status(upload_node.id, "red")
            return

        local_file = os.path.join(project_dir,"release-{0}.tar.gz".format(task_obj.project.title))
        for server in task_obj.project.server.all():
            self.send_deploy_data("上传服务器 %s" %(server))
            rs_upload = self.upload_release_file(local_file,server,task_obj)
            server_node = Node.objects.filter(text=server.hostname, task_id=self.task_id,
                                              server_id=server.id).first()
            if rs_upload:
                self.send_deploy_data("上传服务器 %s 完成" % (server))
                self.node_save(server_node, "green")
                self.update_node_status(server_node.id, "green")
            else:
                self.send_deploy_data("上传服务器 %s 失败" % (server))
                self.node_save(server_node, "red")
                self.update_node_status(server_node.id, "red")
                continue

            #发布前
            if task_obj.before_deploy_script:
                # To do
                rs_pre_deploy = True
                if "bash" in task_obj.before_deploy_script[:40]:
                    try:
                        s_file = os.path.join(script_dir,"before_deploy_script.sh")
                        with open(s_file,"w") as f:
                            f.write(task_obj.before_deploy_script)
                        subprocess.Popen("dos2unix {0}".format(s_file),shell=True)
                        time.sleep(0.1)
                        rs_before_deploy_script = subprocess.Popen("bash {0}".format(s_file),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        self.send_deploy_data(rs_before_deploy_script.stdout.read().decode())
                        self.send_deploy_data(rs_before_deploy_script.stderr.read().decode())
                    except:
                        rs_pre_deploy = False
                        self.send_deploy_data("请检查命令dos2unix  或者文件before_deploy_script.sh是否正常!")
                        

                elif "python" in task_obj.before_deploy_script[:40]:
                    try:
                        s_file = os.path.join(script_dir,"before_deploy_script.py")
                        with open(s_file,"w") as f:
                            f.write(task_obj.before_deploy_script)
                        subprocess.Popen("dos2unix {0}".format(s_file))
                        time.sleep(0.1)
                        rs_before_deploy_script = subprocess.Popen("chmod a+x {0};{1}".format(s_file,s_file))
                        self.send_deploy_data(rs_before_deploy_script.stdout.read().decode())
                        self.send_deploy_data(rs_before_deploy_script.stderr.read().decode())
                    except:
                        rs_pre_deploy = False
                        self.send_deploy_data("请检查命令dos2unix  或者文件before_deploy_script.py是否正常!")
                else:
                    rs_pre_deploy = False
                    self.send_deploy_data("脚本格式不正确，请在首行声明解析器")


                before_deploy_node = Node.objects.filter(text='发布前', task_id=self.task_id, server_id=server.id).first()
                if rs_pre_deploy:
                    self.node_save(before_deploy_node, "green")
                    self.update_node_status(before_deploy_node.id, "green")
                else:
                    self.node_save(before_deploy_node, "red")
                    self.update_node_status(before_deploy_node.id, "red")
                    continue

            if task_obj.after_deploy_script:
                # To do

                rs_after_deploy = True
                if "bash" in task_obj.after_deploy_script[:40]:
                    try:
                        s_file = os.path.join(script_dir, "after_deploy_script.sh")
                        with open(s_file, "w") as f:
                            f.write(task_obj.after_deploy_script)
                        subprocess.Popen("dos2unix {0}".format(s_file), shell=True)
                        time.sleep(0.1)
                        rs_after_deploy_script = subprocess.Popen("bash {0}".format(s_file), shell=True,
                                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        self.send_deploy_data(rs_after_deploy_script.stdout.read().decode())
                        self.send_deploy_data(rs_after_deploy_script.stderr.read().decode())
                    except:
                        rs_after_deploy = False
                        self.send_deploy_data("请检查命令dos2unix  或者文件after_deploy_script.sh是否正常!")

                elif "python" in task_obj.after_deploy_script[:40]:
                    try:
                        s_file = os.path.join(script_dir, "after_deploy_script.py")
                        with open(s_file, "w") as f:
                            f.write(task_obj.before_deploy_script)
                        subprocess.Popen("dos2unix {0}".format(s_file))
                        time.sleep(0.1)
                        rs_after_deploy_script = subprocess.Popen("chmod a+x {0};{1}".format(s_file, s_file))
                        self.send_deploy_data(rs_after_deploy_script.stdout.read().decode())
                        self.send_deploy_data(rs_after_deploy_script.stderr.read().decode())
                    except:
                        rs_after_deploy = False
                        self.send_deploy_data("请检查命令dos2unix  或者文件before_deploy_script.py是否正常!")
                else:
                    rs_after_deploy = False
                    self.send_deploy_data("脚本格式不正确，请在首行声明解析器")

                after_deploy_node = Node.objects.filter(text='发布后', task_id=self.task_id, server_id=server.id).first()
                if rs_after_deploy:
                    self.node_save(after_deploy_node, "green")
                    self.update_node_status(after_deploy_node.id, "green")
                else:
                    self.node_save(after_deploy_node, "red")
                    self.update_node_status(after_deploy_node.id, "red")
                    continue
        if rs_upload & rs_pre_deploy & rs_after_deploy:
            task_obj.status = 3
            self.send_deploy_data("[发布完成] 成功完成，没有出现错误！")
        else:
            task_obj.status = 4
            self.send_deploy_data("[发布完成] 出现错误,请检查！")
        task_obj.save()


    def upload_release_file(self,local_file,server,task_obj,port=SERVER_PORT):
        #指定本地私钥
        rs = True
        try:
            pkey = paramiko.RSAKey.from_private_key_file(SSH_KEY)
            #建立连接
            trans = paramiko.Transport((server,port))
            trans.connect(username=OPS_USER,pkey=pkey)
            sftp = paramiko.SFTPClient.from_transport(trans)
            #发送文件
            sftp.put(localpath=local_file,remotepath=task_obj.project.path)
            #下载数据
            # sftp.get(remotepath=local_file,localpath=local_file)
        except:
            rs = False
        return rs



    def xxx_ooo(self, message):
        data = message['message']
        self.send(data)

    def send_deploy_data(self,result):
        data = {'code': 'deploy',
                'data': result
                }
        data = json.dumps(data)
        async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})

    def update_node_status(self, node_id, status):
        data = json.dumps({'code': 'update', 'node_id': node_id, 'status': status})
        async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})


    def websocket_disconnect(self, message):
        async_to_sync(self.channel_layer.group_discard)(self.task_id, self.channel_name)
        raise StopConsumer()
