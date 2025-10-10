from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("treinos")
        else:
            messages.error(request, "Usuário ou senha inválidos!")

    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def home_view(request):
    return render(request, "treinos.html")


def password_change_request(request):
    """
    Allow a user to change their password by providing username, old password and new password.
    This is intended for a simple 'forgot password' style flow where the user knows their old password.
    """
    User = get_user_model()

    if request.method == 'POST':
        username = request.POST.get('username')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')

        user = authenticate(request, username=username, password=old_password)
        if user is None:
            messages.error(request, 'Nome de usuário ou senha antiga incorretos.')
            return render(request, 'registration/password_change.html')

        # set new password
        user.set_password(new_password)
        user.save()
        messages.success(request, 'Senha alterada com sucesso. Faça login com a nova senha.')
        return redirect('login')

    return render(request, 'registration/password_change.html')
