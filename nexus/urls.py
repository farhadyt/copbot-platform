from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'nexus'

urlpatterns = [
    path('portal/', views.portal_view, name='portal'),
    path('disconnect/', auth_views.LogoutView.as_view(), name='disconnect'),
]