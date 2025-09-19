from django.urls import path
from . import views

urlpatterns = [
    path('', views.treinos_view, name='treinos'),
]