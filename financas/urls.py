from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),

    path("criar-transacao/", views.criar_transacao, name="criar_transacao"),
    path(
        "editar-transacao/<int:pk>/",
        views.editar_transacao,
        name="editar_transacao",
    ),
    path(
        "excluir-transacao/<int:pk>/",
        views.excluir_transacao,
        name="excluir_transacao",
    ),

    path("categorias/", views.listar_categorias, name="listar_categorias"),
    path("categorias/nova/", views.criar_categoria, name="criar_categoria"),
    path(
        "categorias/<int:pk>/editar/",
        views.editar_categoria,
        name="editar_categoria",
    ),
    path(
        "categorias/<int:pk>/excluir/",
        views.excluir_categoria,
        name="excluir_categoria",
    ),

    path("contas/", views.listar_contas, name="listar_contas"),
    path("contas/nova/", views.criar_conta, name="criar_conta"),
    path("contas/<int:pk>/editar/", views.editar_conta, name="editar_conta"),
    path("contas/<int:pk>/excluir/", views.excluir_conta, name="excluir_conta"),

    path("relatorios/", views.relatorios, name="relatorios"),
]