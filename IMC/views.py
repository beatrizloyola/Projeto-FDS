from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from perfil.models import Perfil, Atividade  # reuse existing models
from django.utils import timezone
from datetime import timedelta, date


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
def atividade(request):  # manter o nome para usar na URL 'atividade'
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

	# ====================== AGREGAÇÃO PARA GRÁFICO ======================
	# Construímos dois conjuntos de dados:
	# 1) Mensal (últimas 4 semanas): quantidade de dias distintos em que houve pelo menos um treino concluído em cada bloco de 7 dias.
	# 2) Anual (ano corrente): quantidade de dias distintos com treino em cada mês.
	# Observação: definimos "dia treinado" como "existe ao menos uma Atividade registrada naquele dia".
	now = timezone.localdate()
	# --- Mensal (últimas 4 semanas, em blocos de 7 dias) ---
	start_28 = now - timedelta(days=27)
	ativ_28 = Atividade.objects.filter(usuario=request.user, data__date__gte=start_28, data__date__lte=now)
	datas_28 = {a.data.date() for a in ativ_28}
	semanas_labels = []  # Ex: ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4']
	semanas_values = []  # quantidade de dias treinados distintos
	# Construir da mais antiga para a mais recente
	for i in range(4, 0, -1):  # 4,3,2,1
		idx = i - 1
		week_start = now - timedelta(days=7*idx + 6)
		week_end = now - timedelta(days=7*idx)
		count = sum(1 for d in datas_28 if week_start <= d <= week_end)
		semanas_labels.append(f"Semana {5 - i}")
		semanas_values.append(count)

	# --- Anual (dias treinados por mês no ano corrente) ---
	year = now.year
	ativ_year = Atividade.objects.filter(usuario=request.user, data__year=year)
	datas_year = [a.data.date() for a in ativ_year]
	meses_labels = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
	meses_values = []
	for m in range(1,13):
		unique_days = {d for d in datas_year if d.month == m}
		meses_values.append(len(unique_days))

	# ==================== FIM AGREGAÇÃO ======================

	imc = None
	classificacao = None
	gasto_calorico = None
	agua_recomendada = None

	if perfil.altura_m is None or perfil.peso_kg is None:
		if not msg:
			msg = "Por favor, complete seus dados de altura e peso no perfil."
	elif perfil.altura_m <= 0 or perfil.peso_kg <= 0:
		msg = "Altura e peso inválidos. Atualize suas informações no perfil."
	else:
		imc = float(perfil.peso_kg) / (float(perfil.altura_m) ** 2)
		classificacao = _classificar_imc(imc)
		tmb = 370 + (21.6 * float(perfil.peso_kg))
		gasto_calorico = round(tmb * 1.55, 0)
		agua_recomendada = round(float(perfil.peso_kg) * 35 / 1000, 2)

	contexto = {
		"atividades": atividades,
		"perfil": perfil,
		"imc": imc,
		"classificacao_imc": classificacao,
		"gasto_calorico": gasto_calorico,
		"agua_recomendada": agua_recomendada,
		"msg": msg,
		# Dados do gráfico
		"grafico_mensal_labels": semanas_labels,
		"grafico_mensal_values": semanas_values,
		"grafico_anual_labels": meses_labels,
		"grafico_anual_values": meses_values,
	}
	return render(request, "perfil/atividade.html", contexto)