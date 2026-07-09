from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    CartaoCredito,
    Categoria,
    Conta,
    FaturaCartao,
    MetaFinanceira,
    Transacao,
    TransacaoRecorrente,
)


class FinancasTests(TestCase):
    def setUp(self):
        self.usuario1 = User.objects.create_user(
            username="usuario1",
            password="senha12345",
        )

        self.usuario2 = User.objects.create_user(
            username="usuario2",
            password="senha12345",
        )

        self.conta = Conta.objects.create(
            nome="Nubank",
            tipo=Conta.CONTA_CORRENTE,
            saldo_inicial=Decimal("1000.00"),
            usuario=self.usuario1,
        )

        self.categoria = Categoria.objects.create(
            nome="Salário",
            usuario=self.usuario1,
        )

        self.categoria_despesa = Categoria.objects.create(
            nome="Eletrônicos",
            usuario=self.usuario1,
        )

        self.transacao = Transacao.objects.create(
            descricao="Salário mensal",
            valor=Decimal("3000.00"),
            data=date.today(),
            tipo=Transacao.RECEITA,
            conta=self.conta,
            categoria=self.categoria,
            status=Transacao.PAGO,
            usuario=self.usuario1,
        )

    def login_usuario1(self):
        self.client.login(
            username="usuario1",
            password="senha12345",
        )

    def login_usuario2(self):
        self.client.login(
            username="usuario2",
            password="senha12345",
        )

    def test_dashboard_exige_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)

    def test_usuario_logado_acessa_dashboard(self):
        self.login_usuario1()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_usuario_ve_apenas_suas_transacoes(self):
        self.login_usuario2()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Salário mensal")

    def test_usuario_nao_pode_editar_transacao_de_outro_usuario(self):
        self.login_usuario2()

        response = self.client.get(
            reverse("editar_transacao", args=[self.transacao.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_criar_categoria(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_categoria"),
            {
                "nome": "Alimentação",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Categoria.objects.filter(
                nome="Alimentação",
                usuario=self.usuario1,
            ).exists()
        )

    def test_criar_conta(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_conta"),
            {
                "nome": "Itaú",
                "tipo": Conta.CONTA_CORRENTE,
                "saldo_inicial": "500.00",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Conta.objects.filter(
                nome="Itaú",
                usuario=self.usuario1,
            ).exists()
        )

    def test_criar_transacao_simples(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_transacao"),
            {
                "descricao": "Mercado",
                "valor": "250.00",
                "data": date.today().isoformat(),
                "tipo": Transacao.DESPESA,
                "conta": self.conta.id,
                "cartao": "",
                "categoria": self.categoria_despesa.id,
                "status": Transacao.PAGO,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Transacao.objects.filter(
                descricao="Mercado",
                usuario=self.usuario1,
                valor=Decimal("250.00"),
            ).exists()
        )

    def test_criar_transacao_parcelada(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_transacao"),
            {
                "descricao": "Notebook",
                "valor": "3000.00",
                "data": date.today().isoformat(),
                "tipo": Transacao.DESPESA,
                "conta": self.conta.id,
                "cartao": "",
                "categoria": self.categoria_despesa.id,
                "status": Transacao.PENDENTE,
                "parcelar": "on",
                "quantidade_parcelas": "10",
            },
        )

        self.assertEqual(response.status_code, 302)

        parcelas = Transacao.objects.filter(
            usuario=self.usuario1,
            descricao__startswith="Notebook",
            origem=Transacao.PARCELADA,
        )

        self.assertEqual(parcelas.count(), 10)

        primeira_parcela = parcelas.order_by("numero_parcela").first()

        self.assertEqual(primeira_parcela.numero_parcela, 1)
        self.assertEqual(primeira_parcela.total_parcelas, 10)
        self.assertEqual(primeira_parcela.valor, Decimal("300.00"))

    def test_criar_recorrencia_gera_transacoes(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_recorrencia"),
            {
                "descricao": "Internet",
                "valor": "120.00",
                "data_inicio": date.today().isoformat(),
                "data_fim": "",
                "tipo": TransacaoRecorrente.DESPESA,
                "conta": self.conta.id,
                "categoria": self.categoria_despesa.id,
                "status_padrao": TransacaoRecorrente.PENDENTE,
                "frequencia": TransacaoRecorrente.MENSAL,
                "quantidade_meses": "12",
                "ativa": "on",
            },
        )

        self.assertEqual(response.status_code, 302)

        recorrencia = TransacaoRecorrente.objects.get(
            descricao="Internet",
            usuario=self.usuario1,
        )

        transacoes_geradas = Transacao.objects.filter(
            usuario=self.usuario1,
            recorrencia=recorrencia,
            origem=Transacao.RECORRENTE,
        )

        self.assertEqual(transacoes_geradas.count(), 12)

    def test_criar_cartao(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_cartao"),
            {
                "nome": "Cartão Nubank",
                "limite": "5000.00",
                "dia_fechamento": "5",
                "dia_vencimento": "10",
                "conta_pagamento": self.conta.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            CartaoCredito.objects.filter(
                nome="Cartão Nubank",
                usuario=self.usuario1,
            ).exists()
        )

    def test_compra_no_cartao_cria_fatura(self):
        self.login_usuario1()

        cartao = CartaoCredito.objects.create(
            nome="Cartão Teste",
            limite=Decimal("5000.00"),
            dia_fechamento=5,
            dia_vencimento=10,
            conta_pagamento=self.conta,
            usuario=self.usuario1,
        )

        response = self.client.post(
            reverse("criar_transacao"),
            {
                "descricao": "Compra no cartão",
                "valor": "400.00",
                "data": date.today().isoformat(),
                "tipo": Transacao.DESPESA,
                "conta": "",
                "cartao": cartao.id,
                "categoria": self.categoria_despesa.id,
                "status": Transacao.PENDENTE,
            },
        )

        self.assertEqual(response.status_code, 302)

        transacao = Transacao.objects.get(
            descricao="Compra no cartão",
            usuario=self.usuario1,
        )

        self.assertEqual(transacao.cartao, cartao)
        self.assertEqual(transacao.origem, Transacao.CARTAO)
        self.assertIsNotNone(transacao.fatura)

        self.assertTrue(
            FaturaCartao.objects.filter(
                cartao=cartao,
            ).exists()
        )

    def test_criar_meta_financeira(self):
        self.login_usuario1()

        response = self.client.post(
            reverse("criar_meta"),
            {
                "nome": "Reserva de emergência",
                "valor_alvo": "10000.00",
                "valor_atual": "2500.00",
                "data_limite": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        meta = MetaFinanceira.objects.get(
            nome="Reserva de emergência",
            usuario=self.usuario1,
        )

        self.assertEqual(meta.valor_alvo, Decimal("10000.00"))
        self.assertEqual(meta.valor_atual, Decimal("2500.00"))
        self.assertEqual(meta.percentual, Decimal("25.00"))

    def test_relatorios_exige_login(self):
        response = self.client.get(reverse("relatorios"))

        self.assertEqual(response.status_code, 302)

    def test_usuario_logado_acessa_relatorios(self):
        self.login_usuario1()

        response = self.client.get(reverse("relatorios"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Relatórios Financeiros")

    def test_exportar_excel_exige_login(self):
        response = self.client.get(reverse("exportar_excel"))

        self.assertEqual(response.status_code, 302)

    def test_usuario_logado_exporta_excel(self):
        self.login_usuario1()

        response = self.client.get(reverse("exportar_excel"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_exportar_pdf_exige_login(self):
        response = self.client.get(reverse("exportar_pdf"))

        self.assertEqual(response.status_code, 302)

    def test_usuario_logado_exporta_pdf(self):
        self.login_usuario1()

        response = self.client.get(reverse("exportar_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")