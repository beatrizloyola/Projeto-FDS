from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def medalhas_view(request):
    return render(request, 'medalhas/medalhas.html')