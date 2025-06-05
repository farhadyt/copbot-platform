from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/mirror/(?P<mirror_id>\d+)/$', consumers.MirrorConsumer.as_asgi())
]
