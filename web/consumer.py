import json
from threading import Thread

from channels.generic.websocket import WebsocketConsumer, StopConsumer
from asgiref.sync import async_to_sync
from web.models import Node, DeployTask


class DeployConsumer(WebsocketConsumer):

    def websocket_connect(self, message):
        self.accept()
        self.task_id = self.scope['url_route']['kwargs'].get('task_id')  # session 参数 cookie 等大字典
        print(self.task_id)
        async_to_sync(self.channel_layer.group_add)(self.task_id, self.channel_name)

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
                        before_deploy_node = Node.objects.create(text='发布前',server_id=server.id, task_id=self.task_id, parent=row)
                        node_obj_list.append(before_deploy_node)

                    if task_obj.after_deploy_script:
                        after_deploy_node = Node.objects.create(text='发布后', server_id=server.id,task_id=self.task_id,
                                                                parent=before_deploy_node)
                        node_obj_list.append(after_deploy_node)




            else:
                for row in node_qs:
                    node_obj_list.append(row)


            node_list = []

            for node_obj in node_obj_list:
                temp = {
                    "key": str(node_obj.id),
                    "text": str(node_obj.text),
                    "link_color": "#666666",
                }
                if node_obj.parent:
                    temp["parent"] = str(node_obj.parent_id)
                node_list.append(temp)
                # print(node_list,"----")

            data = json.dumps({'code': 'init', 'data': node_list})
            async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})
        elif txt == 'deploy':
            start_node = Node.objects.filter(text="开始", task_id=self.task_id).first()
            start_node.status = "green"
            start_node.save()
            # data = json.dumps({'code': 'update', 'node_id': start_node.id, 'status': 'green'})
            # async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})
            self.update_node_status(start_node.id,"green")

            if task_obj.before_download_script:
                #To do

                #改变"下载前"node状态
                before_download_node = Node.objects.filter(text='下载前',task_id=self.task_id).first()
                self.update_node_status(before_download_node.id,"green")

            # 改变"下载"node状态
            download_node = Node.objects.filter(text='下载',task_id=self.task_id).first()
            self.update_node_status(download_node.id,"green")

            if task_obj.after_download_script:
                #To do


                # 改变"下载后"node状态
                after_download_node = Node.objects.filter(text='下载后',task_id=self.task_id).first()
                self.update_node_status(after_download_node.id,"green")

            upload_node = Node.objects.filter(text='上传',task_id=self.task_id).first()
            self.update_node_status(upload_node.id,"green")

            for server in task_obj.project.server.all():
                server_node = Node.objects.filter(text=server.hostname,task_id=self.task_id,server_id=server.id).first()
                self.update_node_status(server_node.id,"green")

                if task_obj.before_deploy_script:
                    # To do


                    before_deploy_node = Node.objects.filter(text='发布前',task_id=self.task_id,server_id=server.id).first()
                    self.update_node_status(before_deploy_node.id,"green")

                if task_obj.after_deploy_script:
                    #To do

                    after_deploy_node = Node.objects.filter(text='发布后',task_id=self.task_id,server_id=server.id).first()
                    self.update_node_status(after_deploy_node.id,"green")


    def xxx_ooo(self, message):
        data = message['message']
        self.send(data)

    def update_node_status(self,node_id,status):
        data = json.dumps({'code': 'update', 'node_id': node_id, 'status': status})
        async_to_sync(self.channel_layer.group_send)(self.task_id, {'type': 'xxx.ooo', 'message': data})

    def websocket_disconnect(self, message):
        async_to_sync(self.channel_layer.group_discard)(self.task_id, self.channel_name)
        raise StopConsumer()
