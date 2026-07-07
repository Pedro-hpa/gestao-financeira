import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
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
        {
            "form": form,
            "titulo": "Nova Transação",
        },
    )


@login_required
def editar_transacao(request, pk):
    transacao = get_object_or_404(
        Transacao,
        pk=pk,
        usuario=request.user,
    )

    form = TransacaoForm(
        request.POST or None,
        instance=transacao,
        usuario=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Transação atualizada com sucesso!")
        return redirect("dashboard")

    return render(
        request,
        "financas/criar_transacao.html",
        {
            "form": form,
            "titulo": "Editar Transação",
        },
    )


@login_required
def excluir_transacao(request, pk):
    transacao = get_object_or_404(
        Transacao,
        pk=pk,
        usuario=request.user,
    )

    if request.method == "POST":
        transacao.delete()
        messages.success(request, "Transação excluída com sucesso.")
        return redirect("dashboard")

    return render(
        request,
        "financas/confirmar_exclusao.html",
        {
            "transacao": transacao,
        },
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
        {
            "form": form,
        },
    )


def register(request):
    form = UsuarioCadastroForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cadastro realizado com sucesso! Faça login.")
        return redirect("login")

    return render(
        request,
        "financas/register.html",
        {
            "form": form,
        },
    )


@login_required
def relatorios(request):
    transacoes = Transacao.objects.filter(usuario=request.user)
    categorias = Categoria.objects.filter(usuario=request.user)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    status = request.GET.get("status")

    if data_inicio:
        transacoes = transacoes.filter(data__gte=data_inicio)

    if data_fim:
        transacoes = transacoes.filter(data__lte=data_fim)

    if tipo:
        transacoes = transacoes.filter(tipo=tipo)

    if categoria:
        transacoes = transacoes.filter(categoria_id=categoria)

    if status:
        transacoes = transacoes.filter(status=status)

    total_receitas = transacoes.filter(tipo=Transacao.RECEITA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_despesas = transacoes.filter(tipo=Transacao.DESPESA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    saldo_periodo = total_receitas - total_despesas
    quantidade_transacoes = transacoes.count()

    media_despesas = transacoes.filter(tipo=Transacao.DESPESA).aggregate(
        media=Avg("valor")
    )["media"] or Decimal("0.00")

    maior_receita = (
        transacoes
        .filter(tipo=Transacao.RECEITA)
        .order_by("-valor")
        .first()
    )

    maior_despesa = (
        transacoes
        .filter(tipo=Transacao.DESPESA)
        .order_by("-valor")
        .first()
    )

    movimento_mensal = (
        transacoes
        .annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(
            receitas=Sum("valor", filter=Q(tipo=Transacao.RECEITA)),
            despesas=Sum("valor", filter=Q(tipo=Transacao.DESPESA)),
        )
        .order_by("mes")
    )

    despesas_por_categoria = (
        transacoes
        .filter(tipo=Transacao.DESPESA)
        .values("categoria__nome")
        .annotate(
            total=Sum("valor"),
            quantidade=Count("id"),
        )
        .order_by("-total")
    )

    labels_meses = []
    dados_receitas = []
    dados_despesas = []
    movimento_mensal_lista = []

    for item in movimento_mensal:
        receitas = item["receitas"] or Decimal("0.00")
        despesas = item["despesas"] or Decimal("0.00")
        saldo = receitas - despesas

        labels_meses.append(item["mes"].strftime("%m/%Y"))
        dados_receitas.append(float(receitas))
        dados_despesas.append(float(despesas))

        movimento_mensal_lista.append(
            {
                "mes": item["mes"],
                "receitas": receitas,
                "despesas": despesas,
                "saldo": saldo,
            }
        )

    labels_categorias = []
    dados_categorias = []

    for item in despesas_por_categoria:
        labels_categorias.append(item["categoria__nome"] or "Sem categoria")
        dados_categorias.append(float(item["total"] or 0))

    context = {
        "categorias": categorias,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_periodo": saldo_periodo,
        "quantidade_transacoes": quantidade_transacoes,
        "media_despesas": media_despesas,
        "maior_receita": maior_receita,
        "maior_despesa": maior_despesa,
        "movimento_mensal": movimento_mensal_lista,
        "despesas_por_categoria": despesas_por_categoria,
        "labels_meses_json": json.dumps(labels_meses),
        "dados_receitas_json": json.dumps(dados_receitas),
        "dados_despesas_json": json.dumps(dados_despesas),
        "labels_categorias_json": json.dumps(labels_categorias),
        "dados_categorias_json": json.dumps(dados_categorias),
    }

    return render(request, "financas/relatorios.html", context)