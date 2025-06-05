"""
ASGI config for copbot project with WebSocket support.
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'copbot.settings')
django.setup()

# Now import channels modules after Django is setup
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import pulse.routing

# Create the http application first
http_application = get_asgi_application()

# Then combine with the WebSocket application
application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                pulse.routing.websocket_urlpatterns
            )
        )
    ),
})
