from django.urls import path
from .views import criar_imc, detalhe_imc

urlpatterns = [
    path("novo/", criar_imc, name="criar_imc"),
    path("<int:treino_id>/editar/", detalhe_imc, name="detalhe_imc")
]
