# 🏦 BankReconciler - Sistema de Conciliação Financeira Automatizada

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pytest](https://img.shields.io/badge/Tests-Passing-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-green)
![Pandas](https://img.shields.io/badge/Pandas-ETL-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Sobre o Projeto

Este projeto simula uma rotina real de **Backoffice Bancário**: a conciliação financeira. O objetivo foi criar uma ferramenta que automatiza o cruzamento de dados entre um Core Banking (simulado aqui com PostgreSQL) e arquivos externos de adquirentes, eliminando a conferência manual.

A principal decisão de arquitetura foi tornar o sistema **Database-Driven**. Ao invés de deixar os horários e nomes de arquivos fixos no código Python ("hardcoded"), criei uma tabela de configuração no banco. Isso permite que novas rotinas de conciliação sejam cadastradas ou pausadas via SQL, sem precisar fazer um novo deploy da aplicação.

### O que o projeto resolve?
* **Elimina trabalho manual:** Processa milhares de linhas em segundos usando Pandas.
* **Garante integridade:** Usa transações ACID e tipos de dados decimais para evitar erros de arredondamento financeiro.
* **Auditoria:** Gera relatórios detalhados apontando exatamente onde estão as divergências de centavos ou registros faltantes.

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

O algoritmo de conciliação classifica cada transação em 4 cenários possíveis, baseando-se no cruzamento entre o ID da transação e o valor monetário.

| Status Gerado | Cenário Identificado | Significado para o Negócio |
| :--- | :--- | :--- |
| **CONCILIADO** | `ID` e `Valor` são idênticos nas duas pontas. | Sucesso. O dinheiro que saiu do banco bate com o extrato do parceiro. |
| **DIVERGENCIA VALOR** | O `ID` existe nos dois lados, mas o `Valor` é diferente. | Alerta de Auditoria. Pode indicar erro de taxa, desconto não aplicado ou fraude. |
| **FALTA NO ARQUIVO** | O registro existe no Banco (Supabase), mas não no CSV. | Transação interna sem confirmação externa (ex: Time-out na adquirente). |
| **NAO NO BANCO** | O registro existe no CSV, mas não no Banco. | Transação processada externamente que não foi integrada ao Core Banking. |

## 📂 Estrutura do Projeto

```text
BankReconciler/
├── data/
│   └── extrato_parceiro.csv    # Arquivo de entrada (Simulação de carga externa)
│
├── output/                     # Diretório onde os relatórios .xlsx são salvos
│
├── src/
│   └── main.py                 # Código Principal: Contém o ETL, conexão Supabase e Scheduler
│
├── tests/
│   └── test_conciliacao.py     # Testes Unitários: Validação da lógica de divergência (Pytest)
│
├── .env                        # Arquivo de configuração de senhas (Ignorado pelo Git)
├── .gitignore                  # Lista de exclusão do Git (venv, .env, etc.)
├── requirements.txt            # Lista de dependências do projeto
└── README.md                   # Documentação técnica
```


### 👤 Notas do autor
Desenvolvido com foco em boas práticas de Engenharia de Software e Automação Financeira. ^ ^

[Linkedin](https://www.linkedin.com/in/pedroalves0) | [Email](mailto:pedro.amoura.dev@gmail.com)