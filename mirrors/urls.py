from django.urls import path
from . import views

app_name = 'mirrors'

urlpatterns = [
    path('', views.mirror_list, name='mirror_list'),
    path('create/', views.create_mirror, name='create_mirror'),
    path('<int:pk>/', views.mirror_detail, name='mirror_detail'),
]