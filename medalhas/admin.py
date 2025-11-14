from django.contrib import admin
from .models import Medal, UserMedal


@admin.register(Medal)
class MedalAdmin(admin.ModelAdmin):
	list_display = ('name', 'threshold')
	prepopulated_fields = { 'slug': ('name',) }


@admin.register(UserMedal)
class UserMedalAdmin(admin.ModelAdmin):
	list_display = ('user', 'medal', 'earned_at')
