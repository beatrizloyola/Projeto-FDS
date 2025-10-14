from django.db import models
from django.conf import settings

class Exercicio(models.Model):
    nome = models.CharField(max_length=100)
    gasto_kcal_por_hora = models.FloatField(null=True, blank=True, help_text="Gasto calórico médio por hora")

    def __str__(self):
        return self.nome

class Treino(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"

class TreinoExercicio(models.Model):
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name="itens")
    exercicio = models.ForeignKey(Exercicio, on_delete=models.CASCADE)
    carga = models.IntegerField()
    repeticoes = models.IntegerField()
    descanso = models.IntegerField()
