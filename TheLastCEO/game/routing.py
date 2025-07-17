from django.urls import path
from .consumers import GameConsumer

websocket_urlpatterns = [
    path('ws/game/&lt;uuid:session_id&gt;/', GameConsumer.as_asgi()),
] 