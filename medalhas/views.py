from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from perfil.models import Atividade
from .models import Medal, UserMedal
from django.utils import timezone


@login_required
def medalhas_view(request):
    # count completed trainings for this user
    completions = Atividade.objects.filter(usuario=request.user).count()

    medals = list(Medal.objects.all())
    earned = []
    locked = []
    for m in medals:
        if completions >= m.threshold:
            # ensure UserMedal exists
            um, created = UserMedal.objects.get_or_create(user=request.user, medal=m)
            earned.append({'medal': m, 'earned_at': um.earned_at})
        else:
            progress = int((completions / m.threshold) * 100)
            locked.append({'medal': m, 'progress': progress})

    contexto = {
        'earned': earned,
        'locked': locked,
        'completions': completions,
    }
    return render(request, 'medalhas/medalhas.html', contexto)