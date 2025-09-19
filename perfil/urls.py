from django.urls import path
from . import views

urlpatterns = [
    path('atividade/', views.atividade_view, name='atividade'),
    path('usuario/', views.usuario_view, name='usuario'),
]