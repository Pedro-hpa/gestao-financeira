from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoriaForm, TransacaoForm, UsuarioCadastroForm
from .models import Categoria, Transacao


@login_required
def dashboard(request):
    transacoes = Transacao.objects.filter(usuario=request.user)
    categorias = Categoria.objects.filter(usuario=request.user)

    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    status = request.GET.get("status")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if tipo:
        transacoes = transacoes.filter(tipo=tipo)
    if categoria:
        transacoes = transacoes.filter(categoria_id=categoria)
    if status:
        transacoes = transacoes.filter(status=status)
    if data_inicio:
        transacoes = transacoes.filter(data__gte=data_inicio)
    if data_fim:
        transacoes = transacoes.filter(data__lte=data_fim)

    total_receitas = transacoes.filter(tipo=Transacao.RECEITA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_despesas = transacoes.filter(tipo=Transacao.DESPESA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    saldo_atual = total_receitas - total_despesas

    context = {
        "transacoes": transacoes,
        "categorias": categorias,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_atual": saldo_atual,
    }

    return render(request, "financas/dashboard.html", context)

@login_required
def criar_transacao(request):
    form = TransacaoForm(request.POST or None, usuario=request.user)

    if request.method == "POST" and form.is_valid():
        transacao = form.save(commit=False)
        transacao.usuario = request.user
        transacao.save()
        messages.success(request, "Transação criada com sucesso!")
        return redirect("dashboard")

    return render(
        request,
        "financas/criar_transacao.html",
        {"form": form, "titulo": "Nova Transação"}
    )

@login_required
def editar_transacao(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk, usuario=request.user)
    form = TransacaoForm(
        request.POST or None,
        instance=transacao,
        usuario=request.user
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Transação atualizada com sucesso!")
        return redirect("dashboard")

    return render(
        request,
        "financas/criar_transacao.html",
        {"form": form, "titulo": "Editar Transação"}
    )

@login_required
def criar_categoria(request):
    form = CategoriaForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        categoria = form.save(commit=False)
        categoria.usuario = request.user
        categoria.save()
        messages.success(request, "Categoria criada com sucesso!")
        return redirect("dashboard")

    return render(
        request,
        "financas/criar_categoria.html",
        {"form": form}
    )

@login_required
def excluir_transacao(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk, usuario=request.user)
    if request.method == 'POST':
        transacao.delete()
        messages.success(request, 'Transação excluída com sucesso.')
        return redirect('dashboard')
    return render(request, 'financas/confirmar_exclusao.html', {'transacao': transacao})


def register(request):
    form = UsuarioCadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cadastro realizado com sucesso! Faça login.')
        return redirect('login')
    return render(request, 'financas/register.html', {'form': form})
