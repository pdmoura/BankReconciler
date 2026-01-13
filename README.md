# 🏦 BankReconciler - Sistema de Conciliação Financeira Automatizada

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-green)
![Pandas](https://img.shields.io/badge/Pandas-ETL-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Visão Geral do Projeto
O **BankReconciler** é uma solução de automação de Backoffice desenvolvida para resolver um dos gargalos mais críticos em operações financeiras: a **conciliação de transações**.

A ferramenta atua comparando registros internos (simulando um **Core Banking** via PostgreSQL) com arquivos de extratos de parceiros externos (Adquirentes/Gateways), identificando automaticamente discrepâncias financeiras, taxas incorretas ou transações não processadas.

### 🎯 Diferenciais Técnicos
* **Arquitetura Híbrida:** Processamento local em Python com Banco de Dados na Nuvem (**Supabase/PostgreSQL**).
* **Agendamento Dinâmico (Database-Driven):** As rotinas de execução não são "hardcoded". O robô consulta o banco de dados para saber **quando** rodar e **qual** arquivo processar, permitindo gestão em tempo real via SQL.
* **Segurança:** Credenciais gerenciadas via variáveis de ambiente (`.env`), com tratamento de caracteres especiais e encoding de URL para proteção de senhas.
* **ETL com Pandas:** Utilização de Dataframes para processamento performático de grandes volumes de dados.

---

## ⚙️ Arquitetura da Solução

O fluxo de dados segue o processo de ETL (Extract, Transform, Load):

1.  **Extract:** O robô extrai dados do PostgreSQL (Cloud) e lê arquivos CSV (Legado/Externo).
2.  **Transform:**
    * Normalização de colunas.
    * Cruzamento de dados (Merge/Join).
    * Aplicação de regras de negócio (Cálculo de divergências).
3.  **Load:** Gera relatórios de auditoria em Excel na pasta `/output` e registra logs de execução.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Banco de Dados:** PostgreSQL (Hospedado no Supabase)
* **Bibliotecas Principais:**
    * `pandas` (Análise de Dados)
    * `sqlalchemy` & `psycopg2` (ORM e Conector de Banco)
    * `schedule` (Orquestração de Tarefas)
    * `python-dotenv` (Segurança/Variáveis de Ambiente)
    * `openpyxl` (Exportação Excel)

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Python 3 instalado.
* Conta no Supabase (ou PostgreSQL local).

### 1. Clonar e Instalar
```bash
# Clone o repositório
git clone [https://github.com/SEU_USUARIO/BankReconciler.git](https://github.com/SEU_USUARIO/BankReconciler.git)
cd BankReconciler

# Crie e ative o ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configurar Segurança (.env)
Crie um arquivo .env na raiz do projeto e configure suas credenciais do Supabase. Nota: O sistema possui tratamento automático para senhas com caracteres especiais (ex: #, @).

```bash
DB_HOST=seu-host.supabase.co
DB_NAME=postgres
DB_USER=seu-usuario
DB_PASS="SuaSenhaForteAqui"
DB_PORT=5432
```

### 3. Configurar o Banco de Dados
Execute o script SQL abaixo no seu banco (via Supabase SQL Editor ou DBeaver) para criar a estrutura necessária:

<details> <summary>Clique para ver o Script SQL</summary>

``` sql
-- Tabela de Transações (Core Banking)
CREATE TABLE IF NOT EXISTS transacoes_internas (
    id SERIAL PRIMARY KEY,
    id_transacao VARCHAR(50) UNIQUE NOT NULL,
    data_transacao DATE NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDENTE'
);

-- Tabela de Configuração do Robô (Scheduler)
CREATE TABLE IF NOT EXISTS configuracoes_robo (
    id SERIAL PRIMARY KEY,
    nome_job VARCHAR(50) NOT NULL,
    caminho_arquivo VARCHAR(255) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    horario_execucao TIME NOT NULL
);

-- Dados de Teste
INSERT INTO transacoes_internas (id_transacao, data_transacao, valor) VALUES
('TX001', '2024-01-10', 100.00), 
('TX002', '2024-01-10', 250.50), 
('TX003', '2024-01-11', 50.00);

-- Agendar tarefa (Ajuste o caminho conforme necessário)
INSERT INTO configuracoes_robo (nome_job, caminho_arquivo, horario_execucao) 
VALUES ('Conciliacao_Visa', 'data/extrato.csv', '14:00:00');
```
</details>

### 4. Executar
```bash
python src/main.py
```
O robô iniciará em modo daemon (loop infinito), verificando agendamentos a cada 10 segundos (modo demonstração). Os relatórios serão gerados na pasta output/.

### 📊 Regras de Conciliação (Business Logic)
O sistema classifica automaticamente cada transação em um dos seguintes status:

Status,Descrição,Ação Recomendada
CONCILIADO,ID e Valor batem perfeitamente.,Nenhuma (Sucesso).
DIVERGENCIA VALOR,"O ID existe, mas o valor é diferente.",Auditoria manual (Taxa ou Fraude).
FALTA NO ARQUIVO,"Transação existe no Banco, mas não no Extrato.",Verificar com a Bandeira/Parceiro.
NAO NO BANCO,"Transação está no Extrato, mas não no Sistema Interno.",Verificar erro de integração.


### 👤 Autor
Desenvolvido com foco em boas práticas de Engenharia de Software e Automação Financeira.

[Linkedin](https://www.linkedin.com/in/pedroalves0) | [Email](mailto:pedro.amoura.dev@gmail.com)