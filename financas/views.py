from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import TransacaoForm
from .models import Transacao

@login_required
def dashboard(request):
    transacoes = Transacao.objects.filter(usuario=request.user)

    categoria = request.GET.get('categoria')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if categoria:
        transacoes = transacoes.filter(categoria=categoria)
    if data_inicio:
        transacoes = transacoes.filter(data__gte=data_inicio)
    if data_fim:
        transacoes = transacoes.filter(data__lte=data_fim)

    total_receitas = sum(t.valor for t in transacoes if t.categoria == 'Receita')
    total_despesas = sum(t.valor for t in transacoes if t.categoria == 'Despesa')
    saldo_atual = total_receitas - total_despesas

    context = {
        'transacoes': transacoes,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo_atual': saldo_atual,
    }
    return render(request, 'financas/dashboard.html', context)


@login_required
def criar_transacao(request):
    form = TransacaoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.usuario = request.user
            transacao.save()
            messages.success(request, 'Transação criada com sucesso!')
            return redirect('dashboard')
    return render(request, 'financas/criar_transacao.html', {'form': form})

@login_required
def editar_transacao(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk, usuario=request.user)
    form = TransacaoForm(request.POST or None, instance=transacao)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Transação atualizada com sucesso!')
            return redirect('dashboard')
    return render(request, 'financas/criar_transacao.html', {'form': form})

@login_required
def excluir_transacao(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk, usuario=request.user)
    if request.method == 'POST':
        transacao.delete()
        messages.success(request, 'Transação excluída com sucesso.')
        return redirect('dashboard')
    return render(request, 'financas/confirmar_exclusao.html', {'transacao': transacao})

def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cadastro realizado com sucesso! Faça login.')
        return redirect('login')
    return render(request, 'financas/register.html', {'form': form})
