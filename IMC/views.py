from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from perfil.models import Perfil, Atividade  # reuse existing models


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
	}
	return render(request, "perfil/atividade.html", contexto)