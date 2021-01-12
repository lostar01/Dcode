from channels.routing import ProtocolTypeRouter,URLRouter
from django.conf.urls import url
from web.consumer import DeployConsumer

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        url(r'^publish/(?P<task_id>\d+)/$',DeployConsumer),
    ])
})
