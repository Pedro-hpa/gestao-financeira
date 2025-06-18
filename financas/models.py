from django.db import models
from django.contrib.auth.models import User

class Transacao(models.Model):
    CATEGORIAS = [
        ('Receita', 'Receita'),
        ('Despesa', 'Despesa'),
    ]

    descricao = models.TextField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    categoria = models.CharField(max_length=10, choices=CATEGORIAS)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.descricao} - {self.categoria} - R${self.valor}"
