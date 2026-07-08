from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Categoria, Conta, Transacao


class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ["descricao", "valor", "data", "tipo", "conta", "categoria", "status"]

        labels = {
            "descricao": "Descrição",
            "valor": "Valor",
            "data": "Data",
            "tipo": "Tipo",
            "conta": "Conta / Carteira",
            "categoria": "Categoria",
            "status": "Status",
        }

        widgets = {
            "descricao": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Salário, aluguel, mercado"
            }),
            "valor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01"
            }),
            "data": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "tipo": forms.Select(attrs={
                "class": "form-select"
            }),
            "conta": forms.Select(attrs={
                "class": "form-select"
            }),
            "categoria": forms.Select(attrs={
                "class": "form-select"
            }),
            "status": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        if usuario:
            self.fields["conta"].queryset = usuario.contas.all()
            self.fields["categoria"].queryset = usuario.categorias.all()
        else:
            self.fields["conta"].queryset = Conta.objects.none()
            self.fields["categoria"].queryset = Categoria.objects.none()


class UsuarioCadastroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

        labels = {
            "username": "Usuário",
            "password1": "Senha",
            "password2": "Confirme a senha",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome"]

        labels = {
            "nome": "Nome da categoria",
        }

        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Alimentação, Salário, Transporte"
            }),
        }


class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ["nome", "tipo", "saldo_inicial"]

        labels = {
            "nome": "Nome da conta",
            "tipo": "Tipo",
            "saldo_inicial": "Saldo inicial",
        }

        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Itaú, Nubank, Carteira"
            }),
            "tipo": forms.Select(attrs={
                "class": "form-select"
            }),
            "saldo_inicial": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),
        }