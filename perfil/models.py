from django.db import models
from django.conf import settings

class Perfil(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    bio = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to="perfil/", blank=True, null=True)

    
    altura_m = models.FloatField(null=True, blank=True)  # altura em metros
    peso_kg = models.FloatField(null=True, blank=True)   # peso em kg

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Atividade(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    treino = models.ForeignKey("treinos.Treino", on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} concluiu {self.treino.nome} em {self.data:%d/%m/%Y}"
