from django.urls import path
from . import views

app_name = 'horizon'

urlpatterns = [
    path('', views.command_center, name='index'),
    path('command-center/', views.command_center, name='command_center'),
]