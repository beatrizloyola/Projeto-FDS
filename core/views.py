from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth.hashers import make_password

def cadastro_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        data_nascimento = request.POST.get("data_nascimento")
        altura = request.POST.get("altura")
        peso = request.POST.get("peso")

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Esse nome de usuário já está em uso.")
        else:
            user = CustomUser.objects.create(
                username=username,
                password=make_password(password),
                data_nascimento=data_nascimento,
                altura=altura,
                peso=peso
            )
            login(request, user)
            return redirect("treinos")

    return render(request, "registration/cadastro.html")