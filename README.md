# Gestão Financeira Pessoal

Aplicação web para controle financeiro pessoal, desenvolvida com Django, com autenticação de usuários, cadastro de receitas e despesas, categorias personalizadas, filtros financeiros e dashboard com resumo de saldo.

## Funcionalidades

- Cadastro e login de usuários
- Cadastro de receitas e despesas
- Categorias personalizadas por usuário
- Status de transação: Pago ou Pendente
- Filtros por data, tipo, categoria e status
- Dashboard com total de receitas, despesas e saldo
- Isolamento de dados por usuário autenticado
- Testes automatizados

## Tecnologias

- Python
- Django
- SQLite
- Bootstrap 5
- HTML
- CSS

## Como executar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver