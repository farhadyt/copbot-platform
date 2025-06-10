from django.urls import re_path
from . import consumers
from mirrors import consumers as mirror_consumers

websocket_urlpatterns = [
    re_path(r'ws/mirror/(?P<mirror_id>\d+)/$', consumers.MirrorConsumer.as_asgi()),
    re_path(r'ws/wallet/(?P<agent_id>\d+)/(?P<user_id>\d+)/$', mirror_consumers.AgentConsumer.as_asgi()),
    re_path(r'ws/agent/(?P<agent_id>\d+)/$', mirror_consumers.AgentConsumer.as_asgi()),
]
