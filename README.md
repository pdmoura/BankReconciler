# 🏦 BankReconciler - Sistema de Conciliação Financeira Automatizada

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-green)
![Pandas](https://img.shields.io/badge/Pandas-ETL-orange)
![Automation](https://img.shields.io/badge/RPA-Folder%20Watcher-blueviolet)

## 📌 Sobre o Projeto

Este projeto simula uma rotina real de **Backoffice Bancário**: a conciliação financeira automatizada. Meu objetivo foi criar uma ferramenta resiliente que monitora pastas de rede, detecta novos arquivos de parceiros (CSV) e realiza o cruzamento de dados contra um Core Banking simulado (PostgreSQL) no Supabase.

A arquitetura foi desenhada para ser **Event-Driven (Orientada a Eventos)**: o robô atua como um *Folder Watcher*. Assim que um arquivo é depositado na pasta monitorada, o sistema o processa, gera a conciliação e move o arquivo original para uma pasta de "Processados", garantindo que nenhum dado seja duplicado.

### O que o projeto resolve?
* **Automação de Fluxo:** Detecta, processa e arquiva extratos sem intervenção humana.
* **Integridade de Dados:** Valida transações e aponta divergências (centavos, taxas não previstas).
* **Rastreabilidade:** Mantém histórico completo no banco de dados, incluindo qual arquivo original gerou cada registro.

### 🎯 Diferenciais Técnicos
* **Folder Watcher Inteligente:** Utiliza a biblioteca `glob` para varrer diretórios e processar múltiplos arquivos em lote.
* **Gestão de Arquivos:** Uso de `shutil` e `os` para mover arquivos processados, mantendo o diretório de entrada limpo.
* **Persistência SQL:** Conexão robusta com **Supabase/PostgreSQL** via SQLAlchemy.
* **Configuração Dinâmica:** O robô consulta o banco para saber **quais pastas** monitorar, permitindo alterar o fluxo sem mexer no código Python.

---

## ⚙️ Arquitetura da Solução

O fluxo segue o padrão ETL (Extract, Transform, Load) com gestão de arquivos:

1.  **Monitoramento:** O robô vigia a pasta `data/` a cada 10 segundos.
2.  **Extract & Transform:** Ao encontrar um CSV:
    * Lê o arquivo com Pandas.
    * Cruza com a tabela `transacoes_internas` do banco.
    * Calcula o status (`CONCILIADO`, `DIVERGENCIA`, etc).
3.  **Load & Archive:**
    * Salva o relatório no Banco de Dados e gera backup em Excel na pasta `/output`.
    * **Move o arquivo CSV original** para a pasta `data/processados`, adicionando timestamp ao nome para evitar colisão.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Banco de Dados:** PostgreSQL (Hospedado no Supabase)
* **Core:** `pandas` (ETL), `sqlalchemy` (ORM)
* **Automação:** `schedule` (Loop), `shutil` (Manipulação de Arquivos), `glob` (Pattern Matching)

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Python 3 instalado.
* Conta no Supabase (ou PostgreSQL local).

### 1. Clonar e Instalar
```bash
git clone [https://github.com/SEU_USUARIO/BankReconciler.git](https://github.com/SEU_USUARIO/BankReconciler.git)
cd BankReconciler

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```
### 2. Configurar Segurança (.env)
Crie um arquivo .env na raiz do projeto com as credenciais do banco:

```bash
DB_HOST=seu-host.supabase.co
DB_NAME=postgres
DB_USER=seu-usuario
DB_PASS="SuaSenhaForteAqui"
DB_PORT=5432
```
### 3. Configurar o Banco de Dados (SQL)
Rode este script no Supabase SQL Editor para criar a estrutura compatível com o Folder Watcher:

<details> <summary>Clique para ver o Script SQL Completo</summary>

```sql
-- 1. LIMPEZA
DROP TABLE IF EXISTS historico_conciliacoes;
DROP TABLE IF EXISTS configuracoes_robo;
DROP TABLE IF EXISTS transacoes_internas;

-- 2. CRIAÇÃO DE TABELAS
CREATE TABLE transacoes_internas (
    id_transacao VARCHAR(255) PRIMARY KEY,
    valor NUMERIC(15,2),
    data_transacao DATE
);

CREATE TABLE configuracoes_robo (
    id SERIAL PRIMARY KEY,
    nome_job VARCHAR(50),
    caminho_arquivo TEXT, -- Aponta para a PASTA (ex: 'data/')
    ativo BOOLEAN DEFAULT TRUE
);

CREATE TABLE historico_conciliacoes (
    id SERIAL PRIMARY KEY,
    id_transacao VARCHAR(255),
    valor_banco NUMERIC(15,2),
    valor_arquivo NUMERIC(15,2),
    status VARCHAR(50),
    descricao TEXT,
    data_processamento DATE,
    data_execucao TIMESTAMP DEFAULT NOW(),
    arquivo_origem TEXT
);

-- 3. DADOS INICIAIS
-- O robô vai vigiar a pasta 'data/'
INSERT INTO configuracoes_robo (nome_job, caminho_arquivo) VALUES ('Conciliacao_Geral', 'data/');

-- Dados de Teste
INSERT INTO transacoes_internas (id_transacao, valor, data_transacao) VALUES
('PIX-E001-20240115-A10', 150.50, '2024-01-15'),
('BOL-3490-20240115-B20', 1200.00, '2024-01-15');
```
</details>


### 4. Executar
```
python src/main.py
```
O robô iniciará e ficará aguardando na pasta `data/.`

Arraste um arquivo CSV para a pasta `data/.`

O terminal mostrará o processamento e o arquivo será movido automaticamente para `data/processados`.

### 📊 Regras de Conciliação (Business Logic)

| Status Gerado | Cenário Identificado | Significado para o Negócio |
| :--- | :--- | :--- |
| **OK** | `ID` e `Valor` são idênticos nas duas pontas. | Sucesso. O dinheiro que saiu do banco bate com o extrato do parceiro. |
| **DIVERGENCIA** | O `ID` existe nos dois lados, mas o `Valor` é diferente. | Alerta de Auditoria. Pode indicar erro de taxa, desconto não aplicado ou fraude. |
| **FALTA NO ARQUIVO** | O registro existe no Banco (Supabase), mas não no CSV. | Transação interna sem confirmação externa (ex: Time-out na adquirente). |
| **NAO NO BANCO** | O registro existe no CSV, mas não no Banco. | Transação processada externamente que não foi integrada ao Core Banking. |