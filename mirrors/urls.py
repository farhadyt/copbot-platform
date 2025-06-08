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
]