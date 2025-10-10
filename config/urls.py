"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from config import views
from cadastro.views import cadastro_view

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.login_view, name="login"),
    path("cadastro/", cadastro_view, name="cadastro"),
    path("logout/", views.logout_view, name="logout"),
    path("password_change/", views.password_change_request, name="password_change"),

    path("treinos/", include("treinos.urls")),
    path("medalhas/", include("medalhas.urls")),
    path("perfil/", include("perfil.urls")),
]
