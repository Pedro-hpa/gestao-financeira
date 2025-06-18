from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('criar-transacao/', views.criar_transacao, name='criar_transacao'),
    path('editar-transacao/<int:pk>/', views.editar_transacao, name='editar_transacao'),
    path('excluir-transacao/<int:pk>/', views.excluir_transacao, name='excluir_transacao'),
]
