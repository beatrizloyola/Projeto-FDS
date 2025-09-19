from django.urls import path
from . import views

urlpatterns = [
    path('', views.medalhas_view, name='medalhas'),
]