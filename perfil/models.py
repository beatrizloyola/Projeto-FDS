from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    altura_m = models.DecimalField("Altura (m)", max_digits=4, decimal_places=2, null=True, blank=True)
    peso_kg  = models.DecimalField("Peso (kg)",  max_digits=5, decimal_places=1, null=True, blank=True)

    def _str_(self):
        return f"Perfil de {self.user.username}"