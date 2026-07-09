from django.contrib.auth import views as auth_views
from django.urls import path

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

    # Transações
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

    # Recorrências
    path("recorrencias/", views.listar_recorrencias, name="listar_recorrencias"),
    path("recorrencias/nova/", views.criar_recorrencia, name="criar_recorrencia"),
    path(
        "recorrencias/<int:pk>/editar/",
        views.editar_recorrencia,
        name="editar_recorrencia",
    ),
    path(
        "recorrencias/<int:pk>/excluir/",
        views.excluir_recorrencia,
        name="excluir_recorrencia",
    ),

    # Categorias
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

    # Contas
    path("contas/", views.listar_contas, name="listar_contas"),
    path("contas/nova/", views.criar_conta, name="criar_conta"),
    path(
        "contas/<int:pk>/editar/",
        views.editar_conta,
        name="editar_conta",
    ),
    path(
        "contas/<int:pk>/excluir/",
        views.excluir_conta,
        name="excluir_conta",
    ),

    # Cartões de crédito
    path("cartoes/", views.listar_cartoes, name="listar_cartoes"),
    path("cartoes/novo/", views.criar_cartao, name="criar_cartao"),
    path(
        "cartoes/<int:pk>/editar/",
        views.editar_cartao,
        name="editar_cartao",
    ),
    path(
        "cartoes/<int:pk>/excluir/",
        views.excluir_cartao,
        name="excluir_cartao",
    ),

    # Metas financeiras
    path("metas/", views.listar_metas, name="listar_metas"),
    path("metas/nova/", views.criar_meta, name="criar_meta"),
    path(
        "metas/<int:pk>/editar/",
        views.editar_meta,
        name="editar_meta",
    ),
    path(
        "metas/<int:pk>/excluir/",
        views.excluir_meta,
        name="excluir_meta",
    ),

    # Relatórios
    path("relatorios/", views.relatorios, name="relatorios"),
    path(
        "relatorios/exportar-excel/",
        views.exportar_excel,
        name="exportar_excel",
    ),
    path(
        "relatorios/exportar-pdf/",
        views.exportar_pdf,
        name="exportar_pdf",
    ),
]