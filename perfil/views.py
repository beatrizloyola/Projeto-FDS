from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def atividade_view(request):
    return render(request, 'perfil/atividade.html')

@login_required
def usuario_view(request):
    return render(request, 'perfil/usuario.html')