from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from perfil.models import Perfil
from django.shortcuts import redirect
from django.contrib import messages


@login_required
def usuario_view(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST' and request.POST.get('action') == 'salvar_meta':
        try:
            meta = request.POST.get('meta_calorias', '').strip()
            old_meta = perfil.meta_calorias
            perfil.meta_calorias = int(meta) if meta else None
            if perfil.meta_calorias != old_meta:
                if perfil.meta_calorias:
                    perfil.meta_set_at = timezone.now()
                else:
                    perfil.meta_set_at = None

            perfil.save()
            if perfil.meta_calorias != old_meta:
                messages.success(request, 'Meta de calorias salva. Progresso reiniciado.')
            else:
                messages.success(request, 'Meta de calorias salva.')
        except Exception:
            messages.error(request, 'Valor de meta inválido.')
        return redirect('usuario')

    idade = None
    try:
        data_nasc = request.user.data_nascimento
        if data_nasc:
            today = date.today()
            idade = today.year - data_nasc.year - ((today.month, today.day) < (data_nasc.month, data_nasc.day))
    except Exception:
        idade = None

    tempo_de_uso = None
    try:
        joined = request.user.date_joined
        if joined:
            delta = timezone.localdate() - joined.date()
            tempo_de_uso = delta.days
    except Exception:
        tempo_de_uso = None

    contexto = {
        "perfil": perfil,
        "idade": idade,
        "peso": getattr(request.user, 'peso', perfil.peso_kg if hasattr(perfil, 'peso_kg') else None) ,
        "altura": getattr(request.user, 'altura', perfil.altura_m if hasattr(perfil, 'altura_m') else None),
        "tempo_de_uso": tempo_de_uso,
    }
    return render(request, "perfil/usuario.html", contexto)


@login_required
def editar_usuario(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        data_nascimento = request.POST.get("data_nascimento", "").strip()
        peso = request.POST.get("peso", "").strip()
        altura = request.POST.get("altura", "").strip()

        if first_name is not None:
            request.user.first_name = first_name
        if last_name is not None:
            request.user.last_name = last_name

        invalid_msg = "Os valores são inválidos. Por favor, revise os campos e tente novamente."
        required_msg = "Por favor, preencha todos os campos obrigatórios para calcular seu IMC, gasto calórico e ingestão de água."

        parsed_peso = None
        parsed_altura = None
        invalid = False

        if peso:
            try:
                parsed_peso = float(peso)
                if parsed_peso <= 0:
                    invalid = True
            except Exception:
                invalid = True

        if altura:
            try:
                parsed_altura = float(altura.replace(',','.'))
                if parsed_altura > 10:
                    parsed_altura = round(parsed_altura / 100.0, 2)
                if parsed_altura <= 0:
                    invalid = True
            except Exception:
                invalid = True

        if not peso or not altura:
            messages.error(request, required_msg)
            contexto = {
                'perfil': perfil,
                'first_name': first_name,
                'last_name': last_name,
                'data_nascimento': data_nascimento,
                'altura': altura,
                'peso': peso,
            }
            return render(request, "perfil/editar_usuario.html", contexto)

        if invalid:
            messages.error(request, invalid_msg)
            contexto = {
                'perfil': perfil,
                'first_name': first_name,
                'last_name': last_name,
                'data_nascimento': data_nascimento,
                'altura': altura,
                'peso': peso,
            }
            return render(request, "perfil/editar_usuario.html", contexto)

        try:
            if parsed_peso is not None:
                request.user.peso = parsed_peso
            if parsed_altura is not None:
                request.user.altura = parsed_altura
        except Exception:
            pass
        try:
            if data_nascimento:
                from datetime import datetime
                request.user.data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        except Exception:
            messages.warning(request, "Data de nascimento inválida. Use AAAA-MM-DD.")

        request.user.save()
        try:
            if parsed_peso is not None:
                perfil.peso_kg = parsed_peso
            if parsed_altura is not None:
                perfil.altura_m = parsed_altura
        except Exception:
            pass
        perfil.save()
        messages.success(request, "Informações atualizadas com sucesso.")
        return redirect("usuario")

    contexto = {
        "perfil": perfil,
    }
    return render(request, "perfil/editar_usuario.html", contexto)