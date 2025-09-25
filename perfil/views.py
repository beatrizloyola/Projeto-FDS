from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Atividade, Perfil  


def _classificar_imc(imc: float) -> str:
    if imc < 18.5:   
        return "Abaixo do peso"
    elif 18.5<= imc < 25:   
        return "Peso normal"
    elif 25<= imc < 30:     
        return "Sobrepeso"
    elif 30<= imc < 35:     
        return "Obesidade I"
    elif 35<= imc < 40:     
        return "Obesidade II"
    else:                 
        return "Obesidade III"

@login_required
def atividade_view(request):
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
        return redirect("atividade")  

    atividades = Atividade.objects.filter(usuario=request.user)

    imc = None
    classificacao = None
    if perfil.altura_m and perfil.peso_kg and float(perfil.altura_m) > 0:
        imc = float(perfil.peso_kg) / (float(perfil.altura_m) ** 2)
        classificacao = _classificar_imc(imc)

    context = {
        "atividades": atividades,
        "perfil": perfil,  
        "imc": imc,
        "classificacao_imc": classificacao,
        "msg": msg,
    }
    return render(request, "perfil/atividade.html", context)

@login_required
def usuario_view(request):
    return render(request, "perfil/usuario.html")