from django.contrib import admin
from .models import Transacao

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'valor', 'data', 'usuario')
    search_fields = ('descricao',)
