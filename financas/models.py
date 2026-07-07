from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categorias"
    )
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        unique_together = ["nome", "usuario"]

    def __str__(self):
        return self.nome


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

    descricao = models.CharField(max_length=120)
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    data = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacoes"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PAGO
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transacoes"
    )
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

    def __str__(self):
        return f"{self.descricao} - {self.tipo} - R$ {self.valor}"