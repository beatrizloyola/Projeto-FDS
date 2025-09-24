from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Treino, Exercicio, TreinoExercicio
from perfil.models import Atividade
from django.contrib import messages

@login_required
def treinos_view(request):
    treinos = Treino.objects.filter(usuario=request.user)
    return render(request, 'treinos/treinos.html', {"treinos": treinos})

@login_required
def criar_treino_view(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        treino = Treino.objects.create(usuario=request.user, nome=nome)

        # Vamos pegar os exercícios enviados dinamicamente
        exercicios_ids = request.POST.getlist("exercicio[]")
        cargas = request.POST.getlist("carga[]")
        repeticoes = request.POST.getlist("repeticoes[]")
        descansos = request.POST.getlist("descanso[]")

        for i in range(len(exercicios_ids)):
            if exercicios_ids[i]:  # só cria se tiver algo selecionado
                exercicio = Exercicio.objects.get(id=exercicios_ids[i])
                TreinoExercicio.objects.create(
                    treino=treino,
                    exercicio=exercicio,
                    carga=cargas[i],
                    repeticoes=repeticoes[i],
                    descanso=descansos[i],
                )

        return redirect("treinos")

    exercicios = Exercicio.objects.all()
    return render(request, "treinos/novo_treino.html", {"exercicios": exercicios})

@login_required
def editar_treino_view(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)
    exercicios = Exercicio.objects.all()

    if request.method == "POST":
        treino.nome = request.POST.get("nome", treino.nome)
        treino.save()

        # limpar itens antigos e recriar
        treino.itens.all().delete()

        ids_exercicios = request.POST.getlist("exercicio")
        cargas = request.POST.getlist("carga")
        repeticoes = request.POST.getlist("repeticoes")
        descansos = request.POST.getlist("descanso")

        for i in range(len(ids_exercicios)):
            if ids_exercicios[i]:
                TreinoExercicio.objects.create(
                    treino=treino,
                    exercicio_id=ids_exercicios[i],
                    carga=cargas[i],
                    repeticoes=repeticoes[i],
                    descanso=descansos[i],
                )

        return redirect("treinos")

    return render(
        request,
        "treinos/editar_treino.html",
        {"treino": treino, "exercicios": exercicios},
    )

@login_required
def excluir_treino_view(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)
    if request.method == "POST":
        treino.delete()
        return redirect("treinos")
    return render(request, "treinos/excluir_treino.html", {"treino": treino})

def listar_treinos_view(request):
    treinos = Treino.objects.filter(usuario=request.user)
    return render(request, "treinos/listar_treinos.html", {"treinos": treinos})

@login_required
def concluir_treino_view(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)

    # Se o método for POST, o usuário confirmou no formulário
    if request.method == 'POST':
        Atividade.objects.create(usuario=request.user, treino=treino)
        messages.success(request, f"Parabéns! O treino '{treino.nome}' foi registrado no seu perfil.")
        # Redireciona para a página de perfil (ou para onde fizer sentido)
        return redirect('treinos')

    # Se o método for GET, apenas mostre a página de confirmação
    return render(request, 'treinos/confirmar_conclusao.html', {'treino': treino})
