import json

from channels.generic.websocket import WebsocketConsumer,StopConsumer
from asgiref.sync import async_to_sync
from web.models import Node,DeployTask

class DeployConsumer(WebsocketConsumer):

    def websocket_connect(self, message):
        self.accept()
        self.task_id = self.scope['url_route']['kwargs'].get('task_id')  #session 参数 cookie 等大字典
        print(self.task_id)
        async_to_sync(self.channel_layer.group_add)(self.task_id,self.channel_name)

        

    def websocket_receive(self, message):
        txt = message['text']
        if txt == 'init':
            #创建节点的列表
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
            # 创建节点，并返回前端
            node_qs = Node.objects.filter(task_id=self.task_id)
            if not node_qs:
                start_node = Node.objects.create(text='开始',task_id=self.task_id)
                download_node = Node.objects.create(text='下载',task_id=self.task_id,parent=start_node)

                upload_node = Node.objects.create(text='上传',task_id=self.task_id,parent=download_node)

                task_obj = DeployTask.objects.get(pk=self.task_id)
                for server in task_obj.project.server.all():
                    row = Node.objects.create(text=server.hostname,
                                             task_id=self.task_id,
                                             parent=upload_node,
                                             server=server)
                    node_obj_list.append(row)
            else:
                for row in node_qs:
                    node_obj_list.append(row)

            node_list = []

            for node_obj in node_obj_list:
                temp = {
                    "key": str(node_obj.id),
                    "text": str(node_obj.text),
                    "link_color": "green",
                }
                if node_obj.parent:
                    temp["parent"] = str(node_obj.parent_id)
                node_list.append(temp)
                print(node_list,"----")

            data = json.dumps({'code': 'init', 'data': node_list})
            async_to_sync(self.channel_layer.group_send)(self.task_id,{'type':'xxx.ooo','message':data})

    def xxx_ooo(self,message):
        data = message['message']
        self.send(data)

    def websocket_disconnect(self, message):
        async_to_sync(self.channel_layer.group_discard)(self.task_id,self.channel_name)
        raise StopConsumer()