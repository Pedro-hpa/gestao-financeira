from decimal import Decimal
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Transacao


class TransacaoTests(TestCase):
    def setUp(self):
        self.usuario1 = User.objects.create_user(
            username="usuario1",
            password="senha12345"
        )
        self.usuario2 = User.objects.create_user(
            username="usuario2",
            password="senha12345"
        )

        self.categoria = Categoria.objects.create(
            nome="Salário",
            usuario=self.usuario1
        )

        self.transacao = Transacao.objects.create(
            descricao="Salário mensal",
            valor=Decimal("3000.00"),
            data=date.today(),
            tipo=Transacao.RECEITA,
            categoria=self.categoria,
            status=Transacao.PAGO,
            usuario=self.usuario1
        )

    def test_dashboard_exige_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_usuario_logado_acessa_dashboard(self):
        self.client.login(username="usuario1", password="senha12345")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_usuario_ve_apenas_suas_transacoes(self):
        self.client.login(username="usuario2", password="senha12345")
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "Salário mensal")

    def test_usuario_nao_pode_editar_transacao_de_outro_usuario(self):
        self.client.login(username="usuario2", password="senha12345")
        response = self.client.get(
            reverse("editar_transacao", args=[self.transacao.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_criar_categoria(self):
        self.client.login(username="usuario1", password="senha12345")
        response = self.client.post(
            reverse("criar_categoria"),
            {"nome": "Alimentação"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Categoria.objects.filter(
                nome="Alimentação",
                usuario=self.usuario1
            ).exists()
        )

def test_relatorios_exige_login(self):
    response = self.client.get(reverse("relatorios"))
    self.assertEqual(response.status_code, 302)


def test_usuario_logado_acessa_relatorios(self):
    self.client.login(username="usuario1", password="senha12345")
    response = self.client.get(reverse("relatorios"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Relatórios Financeiros")