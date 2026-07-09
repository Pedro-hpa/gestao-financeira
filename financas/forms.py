from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    CartaoCredito,
    Categoria,
    Conta,
    MetaFinanceira,
    Transacao,
    TransacaoRecorrente,
)


class TransacaoForm(forms.ModelForm):
    parcelar = forms.BooleanField(
        required=False,
        label="Parcelar esta transação?",
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input"
        }),
    )

    quantidade_parcelas = forms.IntegerField(
        required=False,
        min_value=2,
        max_value=60,
        label="Quantidade de parcelas",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "2",
            "max": "60",
            "placeholder": "Ex.: 10",
        }),
    )

    class Meta:
        model = Transacao

        fields = [
            "descricao",
            "valor",
            "data",
            "tipo",
            "conta",
            "cartao",
            "categoria",
            "status",
        ]

        labels = {
            "descricao": "Descrição",
            "valor": "Valor",
            "data": "Data",
            "tipo": "Tipo",
            "conta": "Conta / Carteira",
            "cartao": "Cartão de crédito",
            "categoria": "Categoria",
            "status": "Status",
        }

        widgets = {
            "descricao": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Salário, aluguel, mercado",
            }),
            "valor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
            }),
            "data": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "tipo": forms.Select(attrs={
                "class": "form-select",
            }),
            "conta": forms.Select(attrs={
                "class": "form-select",
            }),
            "cartao": forms.Select(attrs={
                "class": "form-select",
            }),
            "categoria": forms.Select(attrs={
                "class": "form-select",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["conta"].required = False
        self.fields["cartao"].required = False
        self.fields["categoria"].required = False

        self.fields["conta"].empty_label = "Selecione uma conta"
        self.fields["cartao"].empty_label = "Sem cartão de crédito"
        self.fields["categoria"].empty_label = "Sem categoria"

        if usuario:
            self.fields["conta"].queryset = usuario.contas.all()
            self.fields["cartao"].queryset = usuario.cartoes.all()
            self.fields["categoria"].queryset = usuario.categorias.all()
        else:
            self.fields["conta"].queryset = Conta.objects.none()
            self.fields["cartao"].queryset = CartaoCredito.objects.none()
            self.fields["categoria"].queryset = Categoria.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        parcelar = cleaned_data.get("parcelar")
        quantidade_parcelas = cleaned_data.get("quantidade_parcelas")
        conta = cleaned_data.get("conta")
        cartao = cleaned_data.get("cartao")

        if parcelar and not quantidade_parcelas:
            self.add_error(
                "quantidade_parcelas",
                "Informe a quantidade de parcelas."
            )

        if conta and cartao:
            raise forms.ValidationError(
                "Escolha uma conta ou um cartão de crédito, não os dois ao mesmo tempo."
            )

        return cleaned_data


class TransacaoRecorrenteForm(forms.ModelForm):
    class Meta:
        model = TransacaoRecorrente

        fields = [
            "descricao",
            "valor",
            "data_inicio",
            "data_fim",
            "tipo",
            "conta",
            "categoria",
            "status_padrao",
            "frequencia",
            "quantidade_meses",
            "ativa",
        ]

        labels = {
            "descricao": "Descrição",
            "valor": "Valor",
            "data_inicio": "Data de início",
            "data_fim": "Data final",
            "tipo": "Tipo",
            "conta": "Conta / Carteira",
            "categoria": "Categoria",
            "status_padrao": "Status padrão",
            "frequencia": "Frequência",
            "quantidade_meses": "Quantidade de meses",
            "ativa": "Recorrência ativa",
        }

        widgets = {
            "descricao": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Salário, aluguel, internet",
            }),
            "valor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
            }),
            "data_inicio": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "data_fim": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "tipo": forms.Select(attrs={
                "class": "form-select",
            }),
            "conta": forms.Select(attrs={
                "class": "form-select",
            }),
            "categoria": forms.Select(attrs={
                "class": "form-select",
            }),
            "status_padrao": forms.Select(attrs={
                "class": "form-select",
            }),
            "frequencia": forms.Select(attrs={
                "class": "form-select",
            }),
            "quantidade_meses": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "120",
            }),
            "ativa": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["conta"].required = False
        self.fields["categoria"].required = False

        self.fields["conta"].empty_label = "Selecione uma conta"
        self.fields["categoria"].empty_label = "Sem categoria"

        if usuario:
            self.fields["conta"].queryset = usuario.contas.all()
            self.fields["categoria"].queryset = usuario.categorias.all()
        else:
            self.fields["conta"].queryset = Conta.objects.none()
            self.fields["categoria"].queryset = Categoria.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")

        if data_inicio and data_fim and data_fim < data_inicio:
            self.add_error(
                "data_fim",
                "A data final não pode ser anterior à data de início."
            )

        return cleaned_data


class CartaoCreditoForm(forms.ModelForm):
    class Meta:
        model = CartaoCredito

        fields = [
            "nome",
            "limite",
            "dia_fechamento",
            "dia_vencimento",
            "conta_pagamento",
        ]

        labels = {
            "nome": "Nome do cartão",
            "limite": "Limite",
            "dia_fechamento": "Dia de fechamento",
            "dia_vencimento": "Dia de vencimento",
            "conta_pagamento": "Conta de pagamento da fatura",
        }

        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Nubank, Itaú, Inter",
            }),
            "limite": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
            }),
            "dia_fechamento": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "31",
                "placeholder": "Ex.: 5",
            }),
            "dia_vencimento": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "31",
                "placeholder": "Ex.: 10",
            }),
            "conta_pagamento": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["conta_pagamento"].required = False
        self.fields["conta_pagamento"].empty_label = "Selecione uma conta"

        if usuario:
            self.fields["conta_pagamento"].queryset = usuario.contas.all()
        else:
            self.fields["conta_pagamento"].queryset = Conta.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        dia_fechamento = cleaned_data.get("dia_fechamento")
        dia_vencimento = cleaned_data.get("dia_vencimento")

        if dia_fechamento and not 1 <= dia_fechamento <= 31:
            self.add_error(
                "dia_fechamento",
                "Informe um dia entre 1 e 31."
            )

        if dia_vencimento and not 1 <= dia_vencimento <= 31:
            self.add_error(
                "dia_vencimento",
                "Informe um dia entre 1 e 31."
            )

        return cleaned_data


class MetaFinanceiraForm(forms.ModelForm):
    class Meta:
        model = MetaFinanceira

        fields = [
            "nome",
            "valor_alvo",
            "valor_atual",
            "data_limite",
        ]

        labels = {
            "nome": "Nome da meta",
            "valor_alvo": "Valor alvo",
            "valor_atual": "Valor atual",
            "data_limite": "Data limite",
        }

        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Reserva de emergência",
            }),
            "valor_alvo": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
            }),
            "valor_atual": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),
            "data_limite": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        valor_alvo = cleaned_data.get("valor_alvo")
        valor_atual = cleaned_data.get("valor_atual")

        if valor_alvo is not None and valor_atual is not None:
            if valor_atual > valor_alvo:
                self.add_error(
                    "valor_atual",
                    "O valor atual não pode ser maior que o valor alvo."
                )

        return cleaned_data


class UsuarioCadastroForm(UserCreationForm):
    class Meta:
        model = User

        fields = [
            "username",
            "password1",
            "password2",
        ]

        labels = {
            "username": "Usuário",
            "password1": "Senha",
            "password2": "Confirme a senha",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control",
            })


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria

        fields = [
            "nome",
        ]

        labels = {
            "nome": "Nome da categoria",
        }

        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Alimentação, Salário, Transporte",
            }),
        }


class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta

        fields = [
            "nome",
            "tipo",
            "saldo_inicial",
        ]

        labels = {
            "nome": "Nome da conta",
            "tipo": "Tipo",
            "saldo_inicial": "Saldo inicial",
        }

        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Itaú, Nubank, Carteira",
            }),
            "tipo": forms.Select(attrs={
                "class": "form-select",
            }),
            "saldo_inicial": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
            }),
        }