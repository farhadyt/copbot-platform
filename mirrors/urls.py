from django.urls import path
from . import views

app_name = 'mirrors'

urlpatterns = [
    path('', views.mirror_list, name='mirror_list'),
    path('create/', views.create_mirror, name='create_mirror'),
    path('<int:pk>/', views.mirror_detail, name='mirror_detail'),
    path('<int:mirror_pk>/wallet/<str:wallet_id>/', views.wallet_detail, name='wallet_detail'),
    path('<int:pk>/configure-bot/', views.configure_trading_bot, name='configure_bot'),
    path('<int:pk>/toggle-bot/', views.toggle_trading_bot, name='toggle_bot'),
    path('<int:pk>/bot-executions/', views.bot_executions, name='bot_executions'),
    path('wallets/', views.manage_wallets, name='manage_wallets'),
    
    # Agent management URLs
    path('agents/create/<str:agent_type>/', views.create_agent, name='create_agent'),
    path('agents/<int:agent_id>/edit/', views.edit_agent, name='edit_agent'),
    path('agents/<int:agent_id>/delete/', views.delete_agent, name='delete_agent'),
    path('agents/<int:agent_id>/toggle/', views.toggle_agent, name='toggle_agent'),
    path('agents/<int:agent_id>/transactions/', views.agent_transactions, name='agent_transactions'),
]

# WebSocket routing will be handled in the main routing.py file
# This is just a note for the routing patterns needed:
# path('ws/agent/<int:agent_id>/', AgentConsumer.as_asgi()),