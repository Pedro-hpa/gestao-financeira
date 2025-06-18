from django.shortcuts import render, redirect
from .forms import TransacaoForm
from .models import Transacao
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

# Função para o dashboard
@login_required
def dashboard(request):
    transacoes = Transacao.objects.filter(usuario=request.user)
    total_receitas = sum(t.valor for t in transacoes if t.categoria == 'Receita')
    total_despesas = sum(t.valor for t in transacoes if t.categoria == 'Despesa')
    saldo_atual = total_receitas - total_despesas
    context = {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo_atual': saldo_atual,
        'transacoes': transacoes,
    }
    return render(request, 'financas/dashboard.html', context)

# Função para criar transações
# Função para criar transações
@login_required
def criar_transacao(request):
    if request.method == 'POST':
        form = TransacaoForm(request.POST)
        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.usuario = request.user  # Atribui ao usuário logado
            transacao.save()
            messages.success(request, 'Transação criada com sucesso!')
            return redirect('dashboard')  # Redireciona para o dashboard após salvar
        else:
            messages.error(request, 'Erro ao salvar a transação. Verifique os dados.')
    else:
        form = TransacaoForm()
    return render(request, 'financas/criar_transacao.html', {'form': form})


# Função para registrar usuários
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'financas/register.html', {'form': form})
