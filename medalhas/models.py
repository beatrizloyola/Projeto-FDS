from django.db import models
from django.conf import settings


class Medal(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	threshold = models.PositiveIntegerField(help_text='Número de treinos necessários para desbloquear')
	image = models.ImageField(upload_to='medalhas/', blank=True, null=True)

	class Meta:
		ordering = ['threshold']

	def __str__(self):
		return f"{self.name} ({self.threshold})"


class UserMedal(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	medal = models.ForeignKey(Medal, on_delete=models.CASCADE)
	earned_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('user', 'medal')

	def __str__(self):
		return f"{self.user.username} -> {self.medal.name}"
