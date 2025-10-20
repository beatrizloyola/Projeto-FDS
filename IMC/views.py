from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from perfil.models import Perfil, Atividade
from django.utils import timezone
from datetime import timedelta, date
from treinos.models import Exercicio, Treino, TreinoExercicio


def _parse_reps(value):
	if isinstance(value, int):
		return value
	if value is None:
		return 0
	s = str(value)
	for sep in ("–", "-", " "):
		if sep in s:
			parts = s.split(sep)
			for p in parts:
				p = p.strip()
				if p.isdigit():
					return int(p)
	import re
	m = re.search(r"(\d+)", s)
	if m:
		return int(m.group(1))
	return 0


def _create_scheme_for_user(user, scheme):
	from django.db.models import Q
	Treino.objects.filter(usuario=user).filter(
		Q(nome__startswith="Push") | Q(nome__startswith="Pull") | Q(nome__startswith="Legs")
	).delete()

	for treino_nome, itens in scheme.items():
		t = Treino.objects.create(usuario=user, nome=treino_nome)
		for nome_ex, rep, desc in itens:
			ex, _ = Exercicio.objects.get_or_create(nome=nome_ex)
			TreinoExercicio.objects.create(treino=t, exercicio=ex, carga=1, repeticoes=_parse_reps(rep), descanso=_parse_reps(desc))


def _classificar_imc(imc: float) -> str:
	if imc < 18.5:
		return "Abaixo do peso"
	elif 18.5 <= imc < 25:
		return "Peso normal"
	elif 25 <= imc < 30:
		return "Sobrepeso"
	elif 30 <= imc < 35:
		return "Obesidade I"
	elif 35 <= imc < 40:
		return "Obesidade II"
	return "Obesidade III"


@login_required
def atividade(request):
	perfil, _ = Perfil.objects.get_or_create(user=request.user)

	msg = None
	if request.method == "POST" and request.POST.get("acao") == "atualizar_imc":
		alt = (request.POST.get("altura_m") or "").replace(",", ".")
		pes = (request.POST.get("peso_kg") or "").replace(",", ".")
		try:
			alt = float(alt)
			if alt > 10:
				alt = round(alt / 100.0, 2)
			else:
				alt = round(alt, 2)
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

	if request.method == "POST" and request.POST.get("acao") == "atualizar_objetivo":
		obj = request.POST.get("objetivo")
		if obj in ("GANHO", "PERDA", "MANUT"):
			perfil.objetivo = obj
			perfil.save()

			user = request.user
			if obj == "GANHO":
				scheme = {
					"Push (Hipertrofia)": [
						("Supino reto com barra", 8, 90),
						("Desenvolvimento com halteres", 10, 90),
						("Crucifixo inclinado", 12, 60),
						("Tríceps pulley", 12, 60),
						("Elevação lateral", 15, 45),
					],
					"Pull (Hipertrofia)": [
						("Barra fixa / Puxada na polia", 8, 90),
						("Remada curvada com barra", 10, 90),
						("Rosca direta", 12, 60),
						("Face pull", 15, 45),
						("Encolhimento de ombros", 12, 60),
					],
					"Legs (Hipertrofia)": [
						("Agachamento livre", 8, 90),
						("Leg press", 12, 90),
						("Stiff", 10, 90),
						("Extensão de quadríceps", 12, 60),
						("Flexão de pernas (mesa flexora)", 12, 60),
					],
				}
				_create_scheme_for_user(user, scheme)
			elif obj == "PERDA":
				scheme = {
					"Push (Perda de peso)": [
						("Supino reto com halteres", "15", "45"),
						("Desenvolvimento militar", "12–15", "45"),
						("Flexão de braços", "15–20", "30–45"),
						("Tríceps testa", "12", "45"),
						("Elevação lateral", "15", "30"),
					],
					"Pull (Perda de peso)": [
						("Puxada na polia", "15", "45"),
						("Remada baixa na polia", "15", "45"),
						("Rosca martelo", "12–15", "45"),
						("Face pull", "15", "30"),
						("Remada alta com barra", "12", "45"),
					],
					"Legs (Perda de peso)": [
						("Agachamento ou goblet squat", "15", "45–60"),
						("Leg press", "15", "45–60"),
						("Avanço (passada)", "12 cada perna", "45"),
						("Stiff com halteres", "12–15", "45"),
						("Elevação de panturrilha", "20", "30"),
					],
				}
				_create_scheme_for_user(user, scheme)
			elif obj == "MANUT":
				scheme = {
					"Push (Manutenção)": [
						("Supino reto com halteres", "12", "60"),
						("Desenvolvimento com barra", "12", "60"),
						("Crucifixo", "15", "45–60"),
						("Tríceps pulley", "12", "60"),
						("Elevação lateral", "15", "45–60"),
					],
					"Pull (Manutenção)": [
						("Puxada frontal", "12", "60"),
						("Remada curvada com halteres", "12", "60"),
						("Rosca direta", "12", "60"),
						("Face pull", "15", "45–60"),
						("Encolhimento de ombros", "15", "45–60"),
					],
					"Legs (Manutenção)": [
						("Agachamento", "12", "60"),
						("Leg press", "12", "60"),
						("Stiff", "12", "60"),
						("Extensão de pernas", "12", "60"),
						("Flexão de pernas", "12", "60"),
					],
				}
				_create_scheme_for_user(user, scheme)

		return redirect("atividade")

	atividades = Atividade.objects.filter(usuario=request.user)

	now = timezone.localdate()
	start_28 = now - timedelta(days=27)
	ativ_28 = Atividade.objects.filter(usuario=request.user, data__date__gte=start_28, data__date__lte=now)
	datas_28 = {a.data.date() for a in ativ_28}
	semanas_labels = [] 
	semanas_values = []  

	for i in range(4, 0, -1):  
		idx = i - 1
		week_start = now - timedelta(days=7*idx + 6)
		week_end = now - timedelta(days=7*idx)
		count = sum(1 for d in datas_28 if week_start <= d <= week_end)
		semanas_labels.append(f"Semana {5 - i}")
		semanas_values.append(count)

	year = now.year
	ativ_year = Atividade.objects.filter(usuario=request.user, data__year=year)
	datas_year = [a.data.date() for a in ativ_year]
	meses_labels = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
	meses_values = []
	for m in range(1,13):
		unique_days = {d for d in datas_year if d.month == m}
		meses_values.append(len(unique_days))


	imc = None
	classificacao = None
	gasto_calorico = None
	agua_recomendada = None

	# Prepare safe display and calculation values for altura/peso.
	altura_m_display = None
	peso_kg_display = None

	if perfil.altura_m is None or perfil.peso_kg is None:
		if not msg:
			msg = "Por favor, complete seus dados de altura e peso no perfil."
	else:
		# normalize stored altura: if it looks like centimeters (e.g. 150), convert to meters
		try:
			raw_alt = float(perfil.altura_m)
			if raw_alt > 10:
				altura_m_display = round(raw_alt / 100.0, 2)
			else:
				altura_m_display = round(raw_alt, 2)
		except Exception:
			altura_m_display = None

		try:
			peso_kg_display = float(perfil.peso_kg)
		except Exception:
			peso_kg_display = None

		if altura_m_display is None or peso_kg_display is None:
			msg = "Altura e peso inválidos. Atualize suas informações no perfil."
		elif altura_m_display <= 0 or peso_kg_display <= 0:
			msg = "Altura e peso inválidos. Atualize suas informações no perfil."
		else:
			imc = float(peso_kg_display) / (float(altura_m_display) ** 2)
			classificacao = _classificar_imc(imc)
			tmb = 370 + (21.6 * float(peso_kg_display))
			gasto_calorico = round(tmb * 1.55, 0)
			agua_recomendada = round(float(peso_kg_display) * 35 / 1000, 2)

	contexto = {
		"atividades": atividades,
		"perfil": perfil,
		"imc": imc,
		"classificacao_imc": classificacao,
		"gasto_calorico": gasto_calorico,
		"agua_recomendada": agua_recomendada,
		"altura_m_display": altura_m_display,
		"peso_kg_display": peso_kg_display,
		"msg": msg,
		"grafico_mensal_labels": semanas_labels,
		"grafico_mensal_values": semanas_values,
		"grafico_anual_labels": meses_labels,
		"grafico_anual_values": meses_values,
	}
	return render(request, "perfil/atividade.html", contexto)