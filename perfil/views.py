from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Atividade

@login_required
def atividade_view(request):
    atividades = Atividade.objects.filter(usuario=request.user)
    
    context = {
        'atividades': atividades
    }

    return render(request, 'perfil/atividade.html', context)

@login_required
def usuario_view(request):
    return render(request, 'perfil/usuario.html')
