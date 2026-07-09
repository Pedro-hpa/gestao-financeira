import json
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CartaoCreditoForm,
    CategoriaForm,
    ContaForm,
    MetaFinanceiraForm,
    TransacaoForm,
    TransacaoRecorrenteForm,
    UsuarioCadastroForm,
)
from .models import (
    CartaoCredito,
    Categoria,
    Conta,
    FaturaCartao,
    MetaFinanceira,
    Transacao,
    TransacaoRecorrente,
)
from .services import (
    criar_transacoes_parceladas,
    gerar_transacoes_recorrentes,
    obter_alertas_financeiros,
)


def aplicar_filtros_transacoes(request, transacoes):
    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    conta = request.GET.get("conta")
    cartao = request.GET.get("cartao")
    status = request.GET.get("status")
    origem = request.GET.get("origem")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if tipo:
        transacoes = transacoes.filter(tipo=tipo)

    if categoria:
        transacoes = transacoes.filter(categoria_id=categoria)

    if conta:
        transacoes = transacoes.filter(conta_id=conta)

    if cartao:
        transacoes = transacoes.filter(cartao_id=cartao)

    if status:
        transacoes = transacoes.filter(status=status)

    if origem:
        transacoes = transacoes.filter(origem=origem)

    if data_inicio:
        transacoes = transacoes.filter(data__gte=data_inicio)

    if data_fim:
        transacoes = transacoes.filter(data__lte=data_fim)

    return transacoes


def _adicionar_meses_por_ano_mes(ano, mes, quantidade_meses):
    indice_mes = mes - 1 + quantidade_meses
    novo_ano = ano + indice_mes // 12
    novo_mes = indice_mes % 12 + 1

    return novo_ano, novo_mes


def _montar_data_segura(ano, mes, dia):
    ultimo_dia_mes = monthrange(ano, mes)[1]
    dia_seguro = min(dia, ultimo_dia_mes)

    return date(ano, mes, dia_seguro)


def obter_ou_criar_fatura_para_transacao(transacao):
    if not transacao.cartao:
        return None

    cartao = transacao.cartao
    data_compra = transacao.data

    if data_compra.day <= cartao.dia_fechamento:
        ano_fechamento = data_compra.year
        mes_fechamento = data_compra.month
    else:
        ano_fechamento, mes_fechamento = _adicionar_meses_por_ano_mes(
            data_compra.year,
            data_compra.month,
            1,
        )

    data_fechamento = _montar_data_segura(
        ano_fechamento,
        mes_fechamento,
        cartao.dia_fechamento,
    )

    if cartao.dia_vencimento > cartao.dia_fechamento:
        ano_vencimento = ano_fechamento
        mes_vencimento = mes_fechamento
    else:
        ano_vencimento, mes_vencimento = _adicionar_meses_por_ano_mes(
            ano_fechamento,
            mes_fechamento,
            1,
        )

    data_vencimento = _montar_data_segura(
        ano_vencimento,
        mes_vencimento,
        cartao.dia_vencimento,
    )

    fatura, _ = FaturaCartao.objects.get_or_create(
        cartao=cartao,
        mes=data_vencimento.month,
        ano=data_vencimento.year,
        defaults={
            "data_fechamento": data_fechamento,
            "data_vencimento": data_vencimento,
            "status": FaturaCartao.ABERTA,
        },
    )

    return fatura


@login_required
def dashboard(request):
    todas_transacoes = Transacao.objects.filter(usuario=request.user)
    transacoes = aplicar_filtros_transacoes(request, todas_transacoes)

    categorias = Categoria.objects.filter(usuario=request.user)
    contas = Conta.objects.filter(usuario=request.user)
    cartoes = CartaoCredito.objects.filter(usuario=request.user)
    metas = MetaFinanceira.objects.filter(usuario=request.user)[:4]

    hoje = timezone.localdate()

    transacoes_mes = todas_transacoes.filter(
        data__year=hoje.year,
        data__month=hoje.month,
    )

    transacoes_pagas = todas_transacoes.filter(status=Transacao.PAGO)

    total_receitas = transacoes_mes.filter(
        tipo=Transacao.RECEITA,
        status=Transacao.PAGO,
    ).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_despesas = transacoes_mes.filter(
        tipo=Transacao.DESPESA,
        status=Transacao.PAGO,
    ).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_receitas_geral = transacoes_pagas.filter(
        tipo=Transacao.RECEITA,
        cartao__isnull=True,
    ).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_despesas_geral = transacoes_pagas.filter(
        tipo=Transacao.DESPESA,
        cartao__isnull=True,
    ).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    saldo_atual = total_receitas_geral - total_despesas_geral

    contas_com_saldo = []

    for conta_item in contas:
        receitas_conta = conta_item.transacoes.filter(
            usuario=request.user,
            tipo=Transacao.RECEITA,
            status=Transacao.PAGO,
            cartao__isnull=True,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        despesas_conta = conta_item.transacoes.filter(
            usuario=request.user,
            tipo=Transacao.DESPESA,
            status=Transacao.PAGO,
            cartao__isnull=True,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        saldo_conta = conta_item.saldo_inicial + receitas_conta - despesas_conta

        contas_com_saldo.append({
            "conta": conta_item,
            "saldo": saldo_conta,
            "receitas": receitas_conta,
            "despesas": despesas_conta,
        })

    cartoes_com_resumo = []

    for cartao in cartoes:
        fatura_atual = (
            cartao.faturas
            .exclude(status=FaturaCartao.PAGA)
            .order_by("ano", "mes")
            .first()
        )

        total_fatura_atual = Decimal("0.00")

        if fatura_atual:
            total_fatura_atual = fatura_atual.transacoes.filter(
                tipo=Transacao.DESPESA,
            ).aggregate(
                total=Sum("valor")
            )["total"] or Decimal("0.00")

        cartoes_com_resumo.append({
            "cartao": cartao,
            "fatura_atual": fatura_atual,
            "total_fatura_atual": total_fatura_atual,
        })

    context = {
        "transacoes": transacoes,
        "categorias": categorias,
        "contas": contas,
        "cartoes": cartoes,
        "metas": metas,
        "contas_com_saldo": contas_com_saldo,
        "cartoes_com_resumo": cartoes_com_resumo,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_atual": saldo_atual,
        "alertas": obter_alertas_financeiros(request.user),
    }

    return render(request, "financas/dashboard.html", context)


@login_required
def criar_transacao(request):
    form = TransacaoForm(request.POST or None, usuario=request.user)

    if request.method == "POST" and form.is_valid():
        transacao = form.save(commit=False)
        transacao.usuario = request.user

        parcelar = form.cleaned_data.get("parcelar")
        quantidade_parcelas = form.cleaned_data.get("quantidade_parcelas")

        if transacao.cartao:
            transacao.origem = Transacao.CARTAO
            transacao.conta = None
            transacao.fatura = obter_ou_criar_fatura_para_transacao(transacao)

        if parcelar:
            transacoes_criadas = criar_transacoes_parceladas(
                transacao,
                quantidade_parcelas,
            )

            messages.success(
                request,
                f"{len(transacoes_criadas)} parcelas criadas com sucesso!"
            )
        else:
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
        transacao_editada = form.save(commit=False)
        transacao_editada.usuario = request.user

        if transacao_editada.cartao:
            transacao_editada.origem = Transacao.CARTAO
            transacao_editada.conta = None
            transacao_editada.fatura = obter_ou_criar_fatura_para_transacao(
                transacao_editada
            )
        else:
            transacao_editada.fatura = None

        transacao_editada.save()

        messages.success(request, "Transação atualizada com sucesso!")
        return redirect("dashboard")

    return render(
        request,
        "financas/criar_transacao.html",
        {
            "form": form,
            "titulo": "Editar Transação",
            "transacao": transacao,
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
def criar_recorrencia(request):
    form = TransacaoRecorrenteForm(request.POST or None, usuario=request.user)

    if request.method == "POST" and form.is_valid():
        recorrencia = form.save(commit=False)
        recorrencia.usuario = request.user
        recorrencia.save()

        transacoes_criadas = gerar_transacoes_recorrentes(recorrencia)

        messages.success(
            request,
            f"Recorrência criada com sucesso. {len(transacoes_criadas)} lançamentos foram gerados."
        )

        return redirect("listar_recorrencias")

    return render(
        request,
        "financas/criar_recorrencia.html",
        {
            "form": form,
        },
    )


@login_required
def listar_recorrencias(request):
    recorrencias = TransacaoRecorrente.objects.filter(usuario=request.user)

    return render(
        request,
        "financas/listar_recorrencias.html",
        {
            "recorrencias": recorrencias,
        },
    )


@login_required
def editar_recorrencia(request, pk):
    recorrencia = get_object_or_404(
        TransacaoRecorrente,
        pk=pk,
        usuario=request.user,
    )

    form = TransacaoRecorrenteForm(
        request.POST or None,
        instance=recorrencia,
        usuario=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(request, "Recorrência atualizada com sucesso!")
        return redirect("listar_recorrencias")

    return render(
        request,
        "financas/criar_recorrencia.html",
        {
            "form": form,
            "recorrencia": recorrencia,
        },
    )


@login_required
def excluir_recorrencia(request, pk):
    recorrencia = get_object_or_404(
        TransacaoRecorrente,
        pk=pk,
        usuario=request.user,
    )

    if request.method == "POST":
        recorrencia.delete()
        messages.success(request, "Recorrência excluída com sucesso!")

    return redirect("listar_recorrencias")


@login_required
def criar_categoria(request):
    form = CategoriaForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        categoria = form.save(commit=False)
        categoria.usuario = request.user
        categoria.save()

        messages.success(request, "Categoria criada com sucesso!")
        return redirect("listar_categorias")

    return render(
        request,
        "financas/criar_categoria.html",
        {
            "form": form,
        },
    )


@login_required
def listar_categorias(request):
    categorias = Categoria.objects.filter(usuario=request.user)

    categorias_com_totais = []

    for categoria in categorias:
        receitas = categoria.transacoes.filter(
            usuario=request.user,
            tipo=Transacao.RECEITA,
            status=Transacao.PAGO,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        despesas = categoria.transacoes.filter(
            usuario=request.user,
            tipo=Transacao.DESPESA,
            status=Transacao.PAGO,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        saldo = receitas - despesas

        categorias_com_totais.append({
            "categoria": categoria,
            "receitas": receitas,
            "despesas": despesas,
            "saldo": saldo,
        })

    return render(
        request,
        "financas/listar_categorias.html",
        {
            "categorias_com_totais": categorias_com_totais,
        },
    )


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(
        Categoria,
        pk=pk,
        usuario=request.user,
    )

    form = CategoriaForm(request.POST or None, instance=categoria)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoria atualizada com sucesso!")
        return redirect("listar_categorias")

    return render(
        request,
        "financas/criar_categoria.html",
        {
            "form": form,
            "categoria": categoria,
        },
    )


@login_required
def excluir_categoria(request, pk):
    categoria = get_object_or_404(
        Categoria,
        pk=pk,
        usuario=request.user,
    )

    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoria excluída com sucesso!")
        return redirect("listar_categorias")

    return render(
        request,
        "financas/excluir_categoria.html",
        {
            "categoria": categoria,
        },
    )


@login_required
def criar_conta(request):
    form = ContaForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        conta = form.save(commit=False)
        conta.usuario = request.user
        conta.save()

        messages.success(request, "Conta criada com sucesso!")
        return redirect("listar_contas")

    return render(
        request,
        "financas/criar_conta.html",
        {
            "form": form,
        },
    )


@login_required
def listar_contas(request):
    contas = Conta.objects.filter(usuario=request.user)

    contas_com_saldo = []

    for conta in contas:
        receitas = conta.transacoes.filter(
            usuario=request.user,
            tipo=Transacao.RECEITA,
            status=Transacao.PAGO,
            cartao__isnull=True,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        despesas = conta.transacoes.filter(
            usuario=request.user,
            tipo=Transacao.DESPESA,
            status=Transacao.PAGO,
            cartao__isnull=True,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        saldo = conta.saldo_inicial + receitas - despesas

        contas_com_saldo.append({
            "conta": conta,
            "receitas": receitas,
            "despesas": despesas,
            "saldo": saldo,
        })

    return render(
        request,
        "financas/listar_contas.html",
        {
            "contas_com_saldo": contas_com_saldo,
        },
    )


@login_required
def editar_conta(request, pk):
    conta = get_object_or_404(
        Conta,
        pk=pk,
        usuario=request.user,
    )

    form = ContaForm(request.POST or None, instance=conta)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(request, "Conta atualizada com sucesso!")
        return redirect("listar_contas")

    return render(
        request,
        "financas/criar_conta.html",
        {
            "form": form,
            "conta": conta,
        },
    )


@login_required
def excluir_conta(request, pk):
    conta = get_object_or_404(
        Conta,
        pk=pk,
        usuario=request.user,
    )

    if request.method == "POST":
        conta.delete()

        messages.success(request, "Conta excluída com sucesso!")
        return redirect("listar_contas")

    return render(
        request,
        "financas/excluir_conta.html",
        {
            "conta": conta,
        },
    )


@login_required
def listar_cartoes(request):
    cartoes = CartaoCredito.objects.filter(usuario=request.user)

    cartoes_com_resumo = []

    for cartao in cartoes:
        faturas = cartao.faturas.all().order_by("-ano", "-mes")

        total_usado = cartao.transacoes.filter(
            tipo=Transacao.DESPESA,
        ).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")

        fatura_atual = (
            cartao.faturas
            .exclude(status=FaturaCartao.PAGA)
            .order_by("ano", "mes")
            .first()
        )

        total_fatura_atual = Decimal("0.00")

        if fatura_atual:
            total_fatura_atual = fatura_atual.transacoes.filter(
                tipo=Transacao.DESPESA,
            ).aggregate(
                total=Sum("valor")
            )["total"] or Decimal("0.00")

        cartoes_com_resumo.append({
            "cartao": cartao,
            "faturas": faturas,
            "total_usado": total_usado,
            "fatura_atual": fatura_atual,
            "total_fatura_atual": total_fatura_atual,
        })

    return render(
        request,
        "financas/listar_cartoes.html",
        {
            "cartoes_com_resumo": cartoes_com_resumo,
        },
    )


@login_required
def criar_cartao(request):
    form = CartaoCreditoForm(request.POST or None, usuario=request.user)

    if request.method == "POST" and form.is_valid():
        cartao = form.save(commit=False)
        cartao.usuario = request.user
        cartao.save()

        messages.success(request, "Cartão criado com sucesso!")
        return redirect("listar_cartoes")

    return render(
        request,
        "financas/criar_cartao.html",
        {
            "form": form,
        },
    )


@login_required
def editar_cartao(request, pk):
    cartao = get_object_or_404(
        CartaoCredito,
        pk=pk,
        usuario=request.user,
    )

    form = CartaoCreditoForm(
        request.POST or None,
        instance=cartao,
        usuario=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(request, "Cartão atualizado com sucesso!")
        return redirect("listar_cartoes")

    return render(
        request,
        "financas/criar_cartao.html",
        {
            "form": form,
            "cartao": cartao,
        },
    )


@login_required
def excluir_cartao(request, pk):
    cartao = get_object_or_404(
        CartaoCredito,
        pk=pk,
        usuario=request.user,
    )

    if request.method == "POST":
        cartao.delete()
        messages.success(request, "Cartão excluído com sucesso!")

    return redirect("listar_cartoes")


@login_required
def listar_metas(request):
    metas = MetaFinanceira.objects.filter(usuario=request.user)

    return render(
        request,
        "financas/listar_metas.html",
        {
            "metas": metas,
        },
    )


@login_required
def criar_meta(request):
    form = MetaFinanceiraForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        meta = form.save(commit=False)
        meta.usuario = request.user
        meta.save()

        messages.success(request, "Meta criada com sucesso!")
        return redirect("listar_metas")

    return render(
        request,
        "financas/criar_meta.html",
        {
            "form": form,
        },
    )


@login_required
def editar_meta(request, pk):
    meta = get_object_or_404(
        MetaFinanceira,
        pk=pk,
        usuario=request.user,
    )

    form = MetaFinanceiraForm(request.POST or None, instance=meta)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(request, "Meta atualizada com sucesso!")
        return redirect("listar_metas")

    return render(
        request,
        "financas/criar_meta.html",
        {
            "form": form,
            "meta": meta,
        },
    )


@login_required
def excluir_meta(request, pk):
    meta = get_object_or_404(
        MetaFinanceira,
        pk=pk,
        usuario=request.user,
    )

    if request.method == "POST":
        meta.delete()
        messages.success(request, "Meta excluída com sucesso!")

    return redirect("listar_metas")


@login_required
def relatorios(request):
    transacoes = Transacao.objects.filter(usuario=request.user)
    transacoes = aplicar_filtros_transacoes(request, transacoes)

    categorias = Categoria.objects.filter(usuario=request.user)
    contas = Conta.objects.filter(usuario=request.user)
    cartoes = CartaoCredito.objects.filter(usuario=request.user)

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

    resumo_por_conta_query = (
        transacoes
        .values("conta__id", "conta__nome", "conta__tipo")
        .annotate(
            receitas=Sum("valor", filter=Q(tipo=Transacao.RECEITA)),
            despesas=Sum("valor", filter=Q(tipo=Transacao.DESPESA)),
            quantidade=Count("id"),
        )
        .order_by("conta__nome")
    )

    resumo_por_conta = []

    for item in resumo_por_conta_query:
        receitas = item["receitas"] or Decimal("0.00")
        despesas = item["despesas"] or Decimal("0.00")
        saldo = receitas - despesas

        resumo_por_conta.append({
            "conta_id": item["conta__id"],
            "conta_nome": item["conta__nome"] or "Sem conta",
            "conta_tipo": item["conta__tipo"] or "-",
            "receitas": receitas,
            "despesas": despesas,
            "saldo": saldo,
            "quantidade": item["quantidade"],
        })

    resumo_por_cartao_query = (
        transacoes
        .filter(cartao__isnull=False)
        .values("cartao__id", "cartao__nome")
        .annotate(
            total=Sum("valor"),
            quantidade=Count("id"),
        )
        .order_by("cartao__nome")
    )

    resumo_por_cartao = []

    for item in resumo_por_cartao_query:
        resumo_por_cartao.append({
            "cartao_id": item["cartao__id"],
            "cartao_nome": item["cartao__nome"] or "Sem cartão",
            "total": item["total"] or Decimal("0.00"),
            "quantidade": item["quantidade"],
        })

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

        movimento_mensal_lista.append({
            "mes": item["mes"],
            "receitas": receitas,
            "despesas": despesas,
            "saldo": saldo,
        })

    labels_categorias = []
    dados_categorias = []

    for item in despesas_por_categoria:
        labels_categorias.append(item["categoria__nome"] or "Sem categoria")
        dados_categorias.append(float(item["total"] or 0))

    context = {
        "transacoes": transacoes,
        "categorias": categorias,
        "contas": contas,
        "cartoes": cartoes,
        "resumo_por_conta": resumo_por_conta,
        "resumo_por_cartao": resumo_por_cartao,
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


@login_required
def exportar_excel(request):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        messages.error(
            request,
            "A biblioteca openpyxl não está instalada. Adicione openpyxl ao requirements.txt."
        )
        return redirect("relatorios")

    transacoes = Transacao.objects.filter(usuario=request.user)
    transacoes = aplicar_filtros_transacoes(request, transacoes)

    total_receitas = transacoes.filter(tipo=Transacao.RECEITA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_despesas = transacoes.filter(tipo=Transacao.DESPESA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    saldo = total_receitas - total_despesas

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Relatório Financeiro"

    worksheet.append(["Relatório Financeiro"])
    worksheet["A1"].font = Font(bold=True, size=14)

    worksheet.append([])
    worksheet.append(["Resumo"])
    worksheet.append(["Receitas", float(total_receitas)])
    worksheet.append(["Despesas", float(total_despesas)])
    worksheet.append(["Saldo", float(saldo)])

    worksheet.append([])
    worksheet.append([
        "Data",
        "Descrição",
        "Tipo",
        "Categoria",
        "Conta",
        "Cartão",
        "Status",
        "Origem",
        "Parcela",
        "Valor",
    ])

    for cell in worksheet[8]:
        cell.font = Font(bold=True)

    for transacao in transacoes:
        parcela = ""

        if transacao.numero_parcela and transacao.total_parcelas:
            parcela = f"{transacao.numero_parcela}/{transacao.total_parcelas}"

        worksheet.append([
            transacao.data.strftime("%d/%m/%Y"),
            transacao.descricao,
            transacao.tipo,
            transacao.categoria.nome if transacao.categoria else "Sem categoria",
            transacao.conta.nome if transacao.conta else "Sem conta",
            transacao.cartao.nome if transacao.cartao else "Sem cartão",
            transacao.status,
            transacao.origem,
            parcela,
            float(transacao.valor),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="relatorio_financeiro.xlsx"'

    workbook.save(response)

    return response


@login_required
def exportar_pdf(request):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        messages.error(
            request,
            "A biblioteca reportlab não está instalada. Adicione reportlab ao requirements.txt."
        )
        return redirect("relatorios")

    transacoes = Transacao.objects.filter(usuario=request.user)
    transacoes = aplicar_filtros_transacoes(request, transacoes)

    total_receitas = transacoes.filter(tipo=Transacao.RECEITA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_despesas = transacoes.filter(tipo=Transacao.DESPESA).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    saldo = total_receitas - total_despesas

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="relatorio_financeiro.pdf"'

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
    )

    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Relatório Financeiro", estilos["Title"]))
    elementos.append(Spacer(1, 12))

    resumo = [
        ["Receitas", f"R$ {total_receitas:.2f}"],
        ["Despesas", f"R$ {total_despesas:.2f}"],
        ["Saldo", f"R$ {saldo:.2f}"],
    ]

    tabela_resumo = Table(resumo)
    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
    ]))

    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 20))

    dados = [[
        "Data",
        "Descrição",
        "Tipo",
        "Categoria",
        "Conta",
        "Cartão",
        "Status",
        "Valor",
    ]]

    for transacao in transacoes:
        dados.append([
            transacao.data.strftime("%d/%m/%Y"),
            transacao.descricao[:35],
            transacao.tipo,
            transacao.categoria.nome if transacao.categoria else "-",
            transacao.conta.nome if transacao.conta else "-",
            transacao.cartao.nome if transacao.cartao else "-",
            transacao.status,
            f"R$ {transacao.valor:.2f}",
        ])

    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabela)

    documento.build(elementos)

    return response


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