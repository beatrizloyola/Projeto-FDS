from django.db import models
from django.conf import settings
from treinos.models import Treino

class Atividade(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE)
    data_conclusao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} concluiu {self.treino.nome} em {self.data_conclusao.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-data_conclusao']
