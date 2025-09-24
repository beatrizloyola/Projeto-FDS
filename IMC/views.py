from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import IMC


@login_required
def criar_imc(request):
    if request.method == "POST":
        altura = float(request.POST.get("altura"))
        peso = float(request.POST.get("peso"))

        imc = IMC.objects.create(
            usuario=request.user,
            altura=altura,
            peso=peso
        )
        return redirect("detalhe_imc", id=imc.id)

    return render(request, "imc/criar.html")


@login_required
def detalhe_imc(request, id):
    imc = get_object_or_404(IMC, id=id, usuario=request.user)

    valor_imc = round(imc.peso / (imc.altura ** 2), 2)

    if valor_imc < 18.5:
        classificacao = "Baixo peso"
    elif 18.5 <= valor_imc <= 24.99:
        classificacao = "Normal"
    elif 25 <= valor_imc <= 29.99:
        classificacao = "Sobrepeso"
    else:
        classificacao = "Obesidade"

    contexto = {
        "imc": imc,
        "valor_imc": valor_imc,
        "classificacao": classificacao,
    }
    return render(request, "imc/detalhe.html", contexto)