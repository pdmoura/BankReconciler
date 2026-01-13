import pandas as pd
from sqlalchemy import create_engine, text
import os
import schedule
import time
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote_plus

load_dotenv()

# --- CONEXÃO COM SUPABASE ---
try:
    db_pass = quote_plus(os.getenv('DB_PASS'))
    url = f"postgresql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url)
    print("✅ Conectado ao Supabase.")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    exit()

def executar_conciliacao(caminho_csv, nome_job):
    print(f"🔄 Executando: {nome_job}...")
    try:
        with engine.connect() as conn:
            df_banco = pd.read_sql("SELECT id_transacao, valor as valor_banco FROM transacoes_internas", conn)
        
        if not os.path.exists(caminho_csv): return print("Arquivo não encontrado.")
        
        df_csv = pd.read_csv(caminho_csv)
        df_csv.rename(columns={'valor_processado': 'valor_arquivo'}, inplace=True)

        # Cruzamento de dados
        df_final = pd.merge(df_banco, df_csv, on='id_transacao', how='outer', indicator=True)
        
        # Regra de Negócio
        df_final['status'] = df_final.apply(lambda row: 
            'FALTA NO ARQUIVO' if row['_merge'] == 'left_only' else 
            ('NAO NO BANCO' if row['_merge'] == 'right_only' else 
            ('DIVERGENCIA' if row['valor_banco'] != row['valor_arquivo'] else 'OK')), axis=1)

        timestamp = datetime.now().strftime("%H%M%S")
        df_final.to_excel(f"output/{nome_job}_{timestamp}.xlsx", index=False)
        print(f"✅ Relatório gerado em output/")

    except Exception as e: print(f"❌ Erro: {e}")

def iniciar():
    schedule.clear()
    with engine.connect() as conn:
        jobs = conn.execute(text("SELECT nome_job, caminho_arquivo FROM configuracoes_robo WHERE ativo = TRUE")).fetchall()
    
    for job in jobs:
        schedule.every(10).seconds.do(executar_conciliacao, caminho_csv=job[1], nome_job=job[0])
        print(f"📅 Agendado: {job[0]}")

if __name__ == "__main__":
    iniciar()
    while True:
        schedule.run_pending()
        time.sleep(1)