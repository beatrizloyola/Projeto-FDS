from django.urls import path
from .views import criar_treino_view, listar_treinos_view, editar_treino_view, excluir_treino_view

urlpatterns = [
    path("", listar_treinos_view, name="treinos"),
    path("novo/", criar_treino_view, name="criar_treino"),
    path("<int:treino_id>/editar/", editar_treino_view, name="editar_treino"),
    path("<int:treino_id>/excluir/", excluir_treino_view, name="excluir_treino"),
]