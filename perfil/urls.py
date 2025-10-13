from django.urls import path
from . import views
from IMC.views import atividade

urlpatterns = [
    path("usuario/", views.usuario_view, name="usuario"),
    path("usuario/editar/", views.editar_usuario, name="editar_usuario"),
    path("atividade/", atividade, name="atividade"),
]