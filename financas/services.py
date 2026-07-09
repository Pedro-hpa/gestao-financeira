from calendar import monthrange
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from .models import FaturaCartao, Transacao


def adicionar_meses(data_base, quantidade_meses):
    mes = data_base.month - 1 + quantidade_meses
    ano = data_base.year + mes // 12
    mes = mes % 12 + 1
    dia = min(data_base.day, monthrange(ano, mes)[1])

    return data_base.replace(year=ano, month=mes, day=dia)


def montar_data_segura(ano, mes, dia):
    ultimo_dia_mes = monthrange(ano, mes)[1]
    dia_seguro = min(dia, ultimo_dia_mes)

    return timezone.datetime(
        year=ano,
        month=mes,
        day=dia_seguro,
    ).date()


def obter_ou_criar_fatura_para_compra(cartao, data_compra):
    if not cartao:
        return None

    if data_compra.day <= cartao.dia_fechamento:
        data_fechamento = montar_data_segura(
            data_compra.year,
            data_compra.month,
            cartao.dia_fechamento,
        )
    else:
        proximo_mes = adicionar_meses(data_compra, 1)

        data_fechamento = montar_data_segura(
            proximo_mes.year,
            proximo_mes.month,
            cartao.dia_fechamento,
        )

    if cartao.dia_vencimento > cartao.dia_fechamento:
        data_vencimento = montar_data_segura(
            data_fechamento.year,
            data_fechamento.month,
            cartao.dia_vencimento,
        )
    else:
        mes_vencimento = adicionar_meses(data_fechamento, 1)

        data_vencimento = montar_data_segura(
            mes_vencimento.year,
            mes_vencimento.month,
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


@db_transaction.atomic
def gerar_transacoes_recorrentes(recorrencia):
    transacoes_criadas = []

    if not recorrencia.ativa:
        return transacoes_criadas

    for indice in range(recorrencia.quantidade_meses):
        data_lancamento = adicionar_meses(recorrencia.data_inicio, indice)

        if recorrencia.data_fim and data_lancamento > recorrencia.data_fim:
            break

        transacao, criada = Transacao.objects.get_or_create(
            usuario=recorrencia.usuario,
            recorrencia=recorrencia,
            data=data_lancamento,
            defaults={
                "descricao": recorrencia.descricao,
                "valor": recorrencia.valor,
                "tipo": recorrencia.tipo,
                "conta": recorrencia.conta,
                "categoria": recorrencia.categoria,
                "status": recorrencia.status_padrao,
                "origem": Transacao.RECORRENTE,
            },
        )

        if criada:
            transacoes_criadas.append(transacao)

    return transacoes_criadas


@db_transaction.atomic
def criar_transacoes_parceladas(transacao_base, quantidade_parcelas):
    grupo = str(uuid4())
    valor_total = transacao_base.valor

    valor_parcela = (valor_total / Decimal(quantidade_parcelas)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    transacoes_criadas = []

    for numero in range(1, quantidade_parcelas + 1):
        data_parcela = adicionar_meses(transacao_base.data, numero - 1)

        if numero == quantidade_parcelas:
            valor = valor_total - (
                valor_parcela * Decimal(quantidade_parcelas - 1)
            )
        else:
            valor = valor_parcela

        fatura = None
        origem = Transacao.PARCELADA
        conta = transacao_base.conta

        if transacao_base.cartao:
            origem = Transacao.CARTAO
            conta = None
            fatura = obter_ou_criar_fatura_para_compra(
                transacao_base.cartao,
                data_parcela,
            )

        transacao = Transacao.objects.create(
            descricao=f"{transacao_base.descricao} {numero}/{quantidade_parcelas}",
            valor=valor,
            data=data_parcela,
            tipo=transacao_base.tipo,
            conta=conta,
            cartao=transacao_base.cartao,
            fatura=fatura,
            categoria=transacao_base.categoria,
            status=transacao_base.status,
            usuario=transacao_base.usuario,
            origem=origem,
            grupo_parcelamento=grupo,
            numero_parcela=numero,
            total_parcelas=quantidade_parcelas,
        )

        transacoes_criadas.append(transacao)

    return transacoes_criadas


def obter_alertas_financeiros(usuario):
    hoje = timezone.localdate()
    proximos_7_dias = hoje + timedelta(days=7)

    alertas = []

    despesas_pendentes = Transacao.objects.filter(
        usuario=usuario,
        tipo=Transacao.DESPESA,
        status=Transacao.PENDENTE,
        data__range=[hoje, proximos_7_dias],
    ).count()

    if despesas_pendentes:
        alertas.append(
            f"Você tem {despesas_pendentes} despesa(s) pendente(s) nos próximos 7 dias."
        )

    despesas_mes_atual = Transacao.objects.filter(
        usuario=usuario,
        tipo=Transacao.DESPESA,
        data__year=hoje.year,
        data__month=hoje.month,
    ).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    mes_anterior_data = adicionar_meses(hoje, -1)

    despesas_mes_anterior = Transacao.objects.filter(
        usuario=usuario,
        tipo=Transacao.DESPESA,
        data__year=mes_anterior_data.year,
        data__month=mes_anterior_data.month,
    ).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    if despesas_mes_anterior > 0:
        aumento = despesas_mes_atual - despesas_mes_anterior

        if aumento > 0:
            percentual_aumento = (
                aumento / despesas_mes_anterior * Decimal("100")
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            if percentual_aumento >= 30:
                alertas.append(
                    f"Suas despesas aumentaram {percentual_aumento}% em relação ao mês anterior."
                )

    faturas_abertas = FaturaCartao.objects.filter(
        cartao__usuario=usuario,
        status=FaturaCartao.ABERTA,
        data_vencimento__range=[hoje, proximos_7_dias],
    ).count()

    if faturas_abertas:
        alertas.append(
            f"Você tem {faturas_abertas} fatura(s) de cartão vencendo nos próximos 7 dias."
        )

    categorias_mes_atual = (
        Transacao.objects
        .filter(
            usuario=usuario,
            tipo=Transacao.DESPESA,
            data__year=hoje.year,
            data__month=hoje.month,
        )
        .values("categoria__nome")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )

    for categoria in categorias_mes_atual[:3]:
        nome_categoria = categoria["categoria__nome"] or "Sem categoria"
        total_categoria = categoria["total"] or Decimal("0.00")

        if total_categoria > 0:
            alertas.append(
                f"Categoria em destaque este mês: {nome_categoria} com R$ {total_categoria:.2f} em despesas."
            )

    return alertas