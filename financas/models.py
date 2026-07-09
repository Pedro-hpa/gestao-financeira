from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categorias",
    )

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        unique_together = ["nome", "usuario"]

    def __str__(self):
        return self.nome


class Conta(models.Model):
    CONTA_CORRENTE = "Conta corrente"
    CARTEIRA = "Carteira"
    POUPANCA = "Poupança"
    INVESTIMENTO = "Investimento"

    TIPO_CHOICES = [
        (CONTA_CORRENTE, "Conta corrente"),
        (CARTEIRA, "Carteira"),
        (POUPANCA, "Poupança"),
        (INVESTIMENTO, "Investimento"),
    ]

    nome = models.CharField(max_length=100)

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=CONTA_CORRENTE,
    )

    saldo_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="contas",
    )

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Conta"
        verbose_name_plural = "Contas"
        unique_together = ["nome", "usuario"]

    def __str__(self):
        return self.nome


class CartaoCredito(models.Model):
    nome = models.CharField(max_length=100)

    limite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    dia_fechamento = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(31),
        ]
    )

    dia_vencimento = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(31),
        ]
    )

    conta_pagamento = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cartoes",
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cartoes",
    )

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cartão de crédito"
        verbose_name_plural = "Cartões de crédito"
        unique_together = ["nome", "usuario"]

    def __str__(self):
        return self.nome


class FaturaCartao(models.Model):
    ABERTA = "Aberta"
    FECHADA = "Fechada"
    PAGA = "Paga"

    STATUS_CHOICES = [
        (ABERTA, "Aberta"),
        (FECHADA, "Fechada"),
        (PAGA, "Paga"),
    ]

    cartao = models.ForeignKey(
        CartaoCredito,
        on_delete=models.CASCADE,
        related_name="faturas",
    )

    mes = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ]
    )

    ano = models.PositiveIntegerField(
        validators=[MinValueValidator(2000)]
    )

    data_fechamento = models.DateField()

    data_vencimento = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=ABERTA,
    )

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-ano", "-mes"]
        verbose_name = "Fatura do cartão"
        verbose_name_plural = "Faturas do cartão"
        unique_together = ["cartao", "mes", "ano"]

    def __str__(self):
        return f"{self.cartao.nome} - {self.mes:02d}/{self.ano}"


class TransacaoRecorrente(models.Model):
    RECEITA = "Receita"
    DESPESA = "Despesa"

    TIPO_CHOICES = [
        (RECEITA, "Receita"),
        (DESPESA, "Despesa"),
    ]

    PAGO = "Pago"
    PENDENTE = "Pendente"

    STATUS_CHOICES = [
        (PAGO, "Pago"),
        (PENDENTE, "Pendente"),
    ]

    MENSAL = "Mensal"

    FREQUENCIA_CHOICES = [
        (MENSAL, "Mensal"),
    ]

    descricao = models.CharField(max_length=120)

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    data_inicio = models.DateField()

    data_fim = models.DateField(
        null=True,
        blank=True,
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
    )

    conta = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorrencias",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorrencias",
    )

    status_padrao = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDENTE,
    )

    frequencia = models.CharField(
        max_length=20,
        choices=FREQUENCIA_CHOICES,
        default=MENSAL,
    )

    quantidade_meses = models.PositiveIntegerField(
        default=12,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(120),
        ],
    )

    ativa = models.BooleanField(default=True)

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recorrencias",
    )

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["descricao"]
        verbose_name = "Transação recorrente"
        verbose_name_plural = "Transações recorrentes"

    def __str__(self):
        return f"{self.descricao} - {self.frequencia}"


class Transacao(models.Model):
    RECEITA = "Receita"
    DESPESA = "Despesa"

    TIPO_CHOICES = [
        (RECEITA, "Receita"),
        (DESPESA, "Despesa"),
    ]

    PAGO = "Pago"
    PENDENTE = "Pendente"

    STATUS_CHOICES = [
        (PAGO, "Pago"),
        (PENDENTE, "Pendente"),
    ]

    MANUAL = "Manual"
    RECORRENTE = "Recorrente"
    PARCELADA = "Parcelada"
    CARTAO = "Cartão"

    ORIGEM_CHOICES = [
        (MANUAL, "Manual"),
        (RECORRENTE, "Recorrente"),
        (PARCELADA, "Parcelada"),
        (CARTAO, "Cartão"),
    ]

    descricao = models.CharField(max_length=120)

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    data = models.DateField()

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
    )

    conta = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacoes",
    )

    cartao = models.ForeignKey(
        CartaoCredito,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacoes",
    )

    fatura = models.ForeignKey(
        FaturaCartao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacoes",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacoes",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PAGO,
    )

    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default=MANUAL,
    )

    recorrencia = models.ForeignKey(
        TransacaoRecorrente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacoes_geradas",
    )

    grupo_parcelamento = models.CharField(
        max_length=36,
        null=True,
        blank=True,
    )

    numero_parcela = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    total_parcelas = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transacoes",
    )

    criado_em = models.DateTimeField(default=timezone.now)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

    def __str__(self):
        return f"{self.descricao} - {self.tipo} - R$ {self.valor}"


class MetaFinanceira(models.Model):
    nome = models.CharField(max_length=120)

    valor_alvo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    valor_atual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    data_limite = models.DateField(
        null=True,
        blank=True,
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="metas_financeiras",
    )

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["data_limite", "nome"]
        verbose_name = "Meta financeira"
        verbose_name_plural = "Metas financeiras"

    @property
    def percentual(self):
        if not self.valor_alvo:
            return 0

        percentual = (self.valor_atual / self.valor_alvo) * 100
        return round(min(percentual, 100), 2)

    def __str__(self):
        return self.nome