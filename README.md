# Gestão Financeira Pessoal

Aplicação web para controle financeiro pessoal desenvolvida com **Django**, com autenticação de usuários, dashboard financeiro, cadastro de receitas e despesas, contas, categorias, transações recorrentes, parcelamento automático, cartão de crédito, metas financeiras, alertas inteligentes e exportação de relatórios em Excel e PDF.

O objetivo do projeto é simular um sistema real de organização financeira, permitindo que cada usuário acompanhe seus lançamentos, saldos, faturas, metas e relatórios de forma individual e segura.

---

## Funcionalidades

### Autenticação e usuários

* Cadastro de usuários
* Login e logout
* Isolamento de dados por usuário autenticado
* Cada usuário visualiza apenas suas próprias contas, categorias, transações, cartões e metas

---

### Dashboard financeiro

* Resumo de receitas do mês
* Resumo de despesas do mês
* Saldo geral
* Saldos por conta
* Resumo de cartões de crédito
* Fatura atual dos cartões
* Metas financeiras com barra de progresso
* Alertas inteligentes
* Lista de transações recentes
* Filtros por data, tipo, conta, cartão, categoria, status e origem

---

### Transações

* Cadastro de receitas
* Cadastro de despesas
* Edição de transações
* Exclusão de transações
* Status da transação:

  * Pago
  * Pendente
* Classificação por:

  * Conta
  * Cartão de crédito
  * Categoria
  * Tipo
  * Origem

As transações podem ter origem:

* Manual
* Recorrente
* Parcelada
* Cartão

---

### Transações recorrentes

Funcionalidade para cadastrar lançamentos que se repetem mensalmente.

Exemplos:

* Salário
* Aluguel
* Internet
* Academia
* Assinaturas
* Financiamentos

Ao cadastrar uma recorrência, o sistema gera automaticamente os lançamentos futuros com base na quantidade de meses informada.

---

### Parcelamento automático

Permite cadastrar uma compra parcelada e gerar automaticamente todas as parcelas.

Exemplo:

Compra: Notebook
Valor: R$ 3.000,00
Parcelas: 10x

O sistema gera:

* Notebook 1/10 - R$ 300,00
* Notebook 2/10 - R$ 300,00
* Notebook 3/10 - R$ 300,00
* ...
* Notebook 10/10 - R$ 300,00

O sistema também identifica o grupo do parcelamento, número da parcela e total de parcelas.

---

### Cartão de crédito

Funcionalidade para cadastro e acompanhamento de cartões de crédito.

Campos disponíveis:

* Nome do cartão
* Limite
* Dia de fechamento
* Dia de vencimento
* Conta de pagamento da fatura

O sistema permite lançar compras no cartão e associá-las automaticamente à fatura correspondente.

---

### Faturas de cartão

O sistema possui estrutura para controle de faturas.

Status disponíveis:

* Aberta
* Fechada
* Paga

As compras feitas no cartão são agrupadas em faturas com base no dia de fechamento e no dia de vencimento cadastrados.

---

### Contas

* Cadastro de contas
* Edição de contas
* Exclusão de contas
* Saldo inicial
* Tipos de conta:

  * Conta corrente
  * Carteira
  * Poupança
  * Investimento
* Cálculo de saldo por conta

---

### Categorias

* Cadastro de categorias personalizadas
* Edição de categorias
* Exclusão de categorias
* Resumo de receitas, despesas e saldo por categoria

---

### Metas financeiras

Permite cadastrar objetivos financeiros e acompanhar o progresso.

Exemplo:

Meta: Reserva de emergência
Valor alvo: R$ 10.000,00
Valor atual: R$ 4.200,00
Progresso: 42%

Campos disponíveis:

* Nome da meta
* Valor alvo
* Valor atual
* Data limite

---

### Alertas inteligentes

O dashboard exibe alertas automáticos com base nos dados financeiros do usuário.

Exemplos de alertas:

* Despesas pendentes nos próximos 7 dias
* Faturas vencendo nos próximos 7 dias
* Aumento de despesas em relação ao mês anterior
* Categorias com maior gasto no mês

---

### Relatórios

Tela de relatórios com análise financeira detalhada.

Informações exibidas:

* Total de receitas
* Total de despesas
* Saldo do período
* Quantidade de transações
* Média das despesas
* Maior receita
* Maior despesa
* Movimento mensal
* Despesas por categoria
* Resumo por conta
* Resumo por cartão
* Transações filtradas

Filtros disponíveis:

* Data inicial
* Data final
* Tipo
* Conta
* Cartão
* Categoria
* Status
* Origem

---

### Exportação de relatórios

O sistema permite exportar relatórios em:

* Excel
* PDF

O relatório exportado considera os filtros aplicados na tela de relatórios.

---

## Tecnologias utilizadas

* Python
* Django
* SQLite
* Bootstrap 5
* Bootstrap Icons
* HTML
* CSS
* JavaScript
* Chart.js
* OpenPyXL
* ReportLab

---

## Estrutura principal do projeto

```text
gestao-financeira/
├── financas/
│   ├── migrations/
│   ├── templates/
│   │   ├── base.html
│   │   └── financas/
│   │       ├── dashboard.html
│   │       ├── criar_transacao.html
│   │       ├── relatorios.html
│   │       ├── listar_recorrencias.html
│   │       ├── criar_recorrencia.html
│   │       ├── listar_cartoes.html
│   │       ├── criar_cartao.html
│   │       ├── listar_metas.html
│   │       └── criar_meta.html
│   ├── forms.py
│   ├── models.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── static/
│   └── css/
│       └── app.css
├── manage.py
├── requirements.txt
└── README.md
```

---

## Como executar localmente

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd gestao-financeira
```

### 2. Criar ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux/Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Aplicar migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Executar o servidor

```bash
python manage.py runserver
```

Depois acesse:

```text
http://127.0.0.1:8000/
```

---

## Como rodar os testes

```bash
python manage.py test
```

Os testes cobrem:

* Acesso protegido por login
* Isolamento de dados por usuário
* Criação de categorias
* Criação de contas
* Criação de transações simples
* Parcelamento automático
* Transações recorrentes
* Cartão de crédito
* Faturas
* Metas financeiras
* Relatórios
* Exportação em Excel
* Exportação em PDF

---

## Principais modelos

### Categoria

Representa uma categoria financeira personalizada do usuário.

Exemplos:

* Alimentação
* Salário
* Transporte
* Moradia
* Eletrônicos

---

### Conta

Representa uma conta financeira do usuário.

Exemplos:

* Nubank
* Itaú
* Carteira
* Poupança

---

### Transação

Representa uma receita ou despesa.

Pode estar vinculada a:

* Conta
* Cartão
* Categoria
* Recorrência
* Parcelamento
* Fatura

---

### Transação Recorrente

Representa uma regra de repetição mensal para gerar lançamentos futuros.

---

### Cartão de Crédito

Representa um cartão cadastrado pelo usuário, com limite, fechamento, vencimento e conta de pagamento.

---

### Fatura do Cartão

Agrupa compras realizadas no cartão de crédito conforme o período da fatura.

---

### Meta Financeira

Representa um objetivo financeiro com valor alvo, valor atual e percentual de progresso.

---

## Melhorias futuras

Algumas melhorias possíveis para evoluir o projeto:

* Pagamento de fatura com baixa automática no saldo da conta
* Tela detalhada de faturas
* Marcar transações pendentes como pagas
* Exclusão em lote de parcelas
* Edição em lote de recorrências
* Recuperação de senha
* API REST com Django REST Framework
* Deploy em produção
* Banco de dados PostgreSQL
* Gráficos mais avançados
* Modo escuro
* Notificações por e-mail

---

## Objetivo do projeto

Este projeto foi desenvolvido com foco em prática e portfólio, demonstrando conhecimentos em:

* Desenvolvimento web com Django
* Modelagem de dados
* Autenticação de usuários
* Relacionamentos entre modelos
* Regras de negócio
* Formulários
* Views protegidas por login
* Templates com Bootstrap
* Testes automatizados
* Exportação de arquivos
* Organização de código em services
* Isolamento de dados por usuário
* Criação de funcionalidades próximas de um sistema financeiro real

---

## Autor

Projeto desenvolvido como aplicação de estudo e portfólio em Django.
