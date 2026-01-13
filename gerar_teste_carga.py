import pandas as pd
import random
import os

# Configuração
QTD_LINHAS = 10000
CAMINHO_ARQUIVO = "data/extrato_teste_carga.csv"

print(f"Gerando arquivo com {QTD_LINHAS} transações...")

dados = []
for i in range(QTD_LINHAS):
    # Gera dados aleatórios
    transacao = {
        "id_transacao": f"TX-CARGA-{i}",
        "data_processamento": "2024-01-20",
        "valor_processado": round(random.uniform(10.0, 5000.0), 2),
        "descricao": f"Transacao de Teste de Carga {i}"
    }
    dados.append(transacao)

df = pd.DataFrame(dados)
df.to_csv(CAMINHO_ARQUIVO, index=False)

print(f"✅ Arquivo gerado: {CAMINHO_ARQUIVO}")
print("Agora rode o 'python src/main.py' e teste sua eficiência!")