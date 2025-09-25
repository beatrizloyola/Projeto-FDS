# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Perfil  

@login_required
def atividade(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    msg = None

    if request.method == "POST" and request.POST.get("acao") == "atualizar_imc":
        alt = (request.POST.get("altura_m") or "").replace(",", ".")
        pes = (request.POST.get("peso_kg") or "").replace(",", ".")
        try:
            alt = round(float(alt), 2)
            pes = round(float(pes), 1)
            if alt <= 0 or pes <= 0:
                raise ValueError
        except Exception:
            msg = "Informe altura e peso válidos."
        else:
            perfil.altura_m = alt
            perfil.peso_kg = pes
            perfil.save()
            msg = "IMC atualizado com sucesso."

    imc = None
    classificacao = None
    if perfil.altura_m and perfil.peso_kg and perfil.altura_m > 0:
        imc = float(perfil.peso_kg) / (float(perfil.altura_m) ** 2)
        if imc < 18.5:   classificacao = "Abaixo do peso"
        elif imc < 25:   classificacao = "Peso normal"
        elif imc < 30:   classificacao = "Sobrepeso"
        elif imc < 35:   classificacao = "Obesidade I"
        elif imc < 40:   classificacao = "Obesidade II"
        else:            classificacao = "Obesidade III"

   
    contexto = {
        "perfil": perfil,
        "imc": imc,
        "classificacao_imc": classificacao,
        "msg": msg,
        
    }
    return render(request, "perfil/atividade.html", contexto)