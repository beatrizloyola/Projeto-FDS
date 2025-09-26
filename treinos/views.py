from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Treino, Exercicio, TreinoExercicio
from perfil.models import Atividade
from django.contrib import messages
from django.http import JsonResponse

@login_required
def treinos_view(request):
    treinos = Treino.objects.filter(usuario=request.user)
    return render(request, 'treinos/treinos.html', {"treinos": treinos})

@login_required
def criar_treino_view(request):
    if request.method == "POST":
        nome = request.POST.get("nome", "").strip() or "Treino"
        treino = Treino.objects.create(usuario=request.user, nome=nome)

        exercicios_ids = request.POST.getlist("exercicio[]")
        cargas = request.POST.getlist("carga[]")
        repeticoes = request.POST.getlist("repeticoes[]")
        descansos = request.POST.getlist("descanso[]")

        created_items = []
        for i in range(len(exercicios_ids)):
            if exercicios_ids[i]:
                ex = Exercicio.objects.filter(id=exercicios_ids[i]).first()
                if not ex:
                    continue
                item = TreinoExercicio.objects.create(
                    treino=treino,
                    exercicio=ex,
                    carga=cargas[i] if i < len(cargas) else "",
                    repeticoes=repeticoes[i] if i < len(repeticoes) else "",
                    descanso=descansos[i] if i < len(descansos) else "",
                )
                created_items.append(item)

        # Suporte AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "ok": True,
                "treino": {
                    "id": treino.id,
                    "nome": treino.nome,
                    "exercicios": [
                        {
                            "id": it.id,
                            "exercicio_id": it.exercicio.id,
                            "exercicio_nome": it.exercicio.nome,
                            "carga": it.carga,
                            "repeticoes": it.repeticoes,
                            "descanso": it.descanso,
                        } for it in created_items
                    ]
                }
            })

        return redirect("treinos")

    exercicios = Exercicio.objects.all().order_by("nome")
    return render(request, "treinos/novo_treino.html", {"exercicios": exercicios})

@login_required
def editar_treino_view(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)
    exercicios = Exercicio.objects.all().order_by("nome")

    if request.method == "POST":
        treino.nome = request.POST.get("nome", treino.nome)
        treino.save()

        # limpar itens antigos e recriar (simplificação)
        treino.itens.all().delete()

        ids_exercicios = request.POST.getlist("exercicio[]") or request.POST.getlist("exercicio")
        cargas = request.POST.getlist("carga[]") or request.POST.getlist("carga")
        repeticoes = request.POST.getlist("repeticoes[]") or request.POST.getlist("repeticoes")
        descansos = request.POST.getlist("descanso[]") or request.POST.getlist("descanso")

        created_items = []
        for i in range(len(ids_exercicios)):
            if ids_exercicios[i]:
                item = TreinoExercicio.objects.create(
                    treino=treino,
                    exercicio_id=ids_exercicios[i],
                    carga=cargas[i] if i < len(cargas) else "",
                    repeticoes=repeticoes[i] if i < len(repeticoes) else "",
                    descanso=descansos[i] if i < len(descansos) else "",
                )
                created_items.append(item)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "ok": True,
                "treino": {
                    "id": treino.id,
                    "nome": treino.nome,
                    "exercicios": [
                        {
                            "id": it.id,
                            "exercicio_id": it.exercicio.id,
                            "exercicio_nome": it.exercicio.nome,
                            "carga": it.carga,
                            "repeticoes": it.repeticoes,
                            "descanso": it.descanso,
                        } for it in created_items
                    ]
                }
            })

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

@login_required
def listar_treinos_view(request):
    from django.utils import timezone
    from django.db.models import Prefetch
    hoje = timezone.localdate()
    treinos = (
        Treino.objects.filter(usuario=request.user)
        .prefetch_related(
            Prefetch(
                "itens",
                queryset=TreinoExercicio.objects.select_related("exercicio"),
            )
        )
        .order_by("nome")
    )
    # Mapear ids de treinos feitos hoje
    feitos_ids = set(
        Atividade.objects.filter(
            usuario=request.user, data__date=hoje
        ).values_list("treino_id", flat=True)
    )
    exercicios = Exercicio.objects.all().order_by("nome")
    return render(
        request,
        "treinos/listar_treinos.html",
        {"treinos": treinos, "treinos_feitos_hoje": feitos_ids, "data_hoje": hoje, "exercicios": exercicios},
    )

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
