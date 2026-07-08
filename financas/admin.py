from django.contrib import admin

from .models import Categoria, Conta, Transacao


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "tipo", "categoria", "conta", "valor", "data", "usuario")
    search_fields = ("descricao",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "usuario", "criado_em")
    search_fields = ("nome",)


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "saldo_inicial", "usuario", "criado_em")
    search_fields = ("nome",)