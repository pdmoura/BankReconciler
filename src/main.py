import pandas as pd
from sqlalchemy import create_engine, text
import os
import schedule
import time
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote_plus
import shutil
import glob

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

def processar_conciliacao(df_banco, df_csv):
    """
    Função Pura: Recebe DataFrames, aplica regras e retorna o resultado.
    Isolada para facilitar os testes unitários.
    """
    # Cruzamento de dados (Outer Join)
    df_final = pd.merge(df_banco, df_csv, on='id_transacao', how='outer', indicator=True)
    
    # Regra de Negócio
    df_final['status'] = df_final.apply(lambda row: 
        'FALTA NO ARQUIVO' if row['_merge'] == 'left_only' else 
        ('NAO NO BANCO' if row['_merge'] == 'right_only' else 
        ('DIVERGENCIA' if row['valor_banco'] != row['valor_arquivo'] else 'OK')), axis=1)
        
    return df_final

# --- FUNÇÃO DO ROBÔ (ORQUESTRADOR) ---
def executar_conciliacao(pasta_monitorada, nome_job):
    # 1. Busca INTELIGENTE: Pega qualquer arquivo .csv na pasta
    arquivos_encontrados = glob.glob(os.path.join(pasta_monitorada, "*.csv"))

    if not arquivos_encontrados:
        return # Silêncio: Nenhum arquivo na pasta

    print(f"🔄 Encontrei {len(arquivos_encontrados)} arquivo(s) na pasta {pasta_monitorada}!")

    # Carrega dados do Banco
    try:
        with engine.connect() as conn:
            df_banco = pd.read_sql("SELECT id_transacao, valor as valor_banco FROM transacoes_internas", conn)
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")
        return

    # 2. Processa cada arquivo encontrado
    for caminho_arquivo in arquivos_encontrados:
        try:
            print(f"   📄 Processando: {os.path.basename(caminho_arquivo)}...")
            
            df_csv = pd.read_csv(caminho_arquivo)
            
            # Normalização de nomes de colunas
            if 'valor_processado' in df_csv.columns:
                df_csv.rename(columns={'valor_processado': 'valor_arquivo'}, inplace=True)
            elif 'valor' in df_csv.columns:
                df_csv.rename(columns={'valor': 'valor_arquivo'}, inplace=True)

            # Lógica de Negócio
            df_final = processar_conciliacao(df_banco, df_csv)
            
            # Metadata
            df_final['data_execucao'] = datetime.now()
            df_final['arquivo_origem'] = os.path.basename(caminho_arquivo)

            # Salvar Excel (Backup)
            timestamp = datetime.now().strftime("%H%M%S")
            nome_limpo = os.path.basename(caminho_arquivo).replace('.csv', '')
            os.makedirs("output", exist_ok=True)
            df_final.to_excel(f"output/{nome_limpo}_{timestamp}.xlsx", index=False)
            
            # Salvar no Banco (Supabase)
            colunas_do_banco = ['id_transacao', 'valor_banco', 'valor_arquivo', 'status', 'descricao', 'data_processamento', 'data_execucao', 'arquivo_origem']
            cols_to_save = [c for c in colunas_do_banco if c in df_final.columns]
            
            df_final[cols_to_save].to_sql('historico_conciliacoes', engine, if_exists='append', index=False)

            # Mover para Processados
            pasta_destino = os.path.join(pasta_monitorada, "processados")
            os.makedirs(pasta_destino, exist_ok=True)
            
            timestamp_arq = datetime.now().strftime("%Y%m%d_%H%M%S")
            novo_nome = f"{timestamp_arq}_{os.path.basename(caminho_arquivo)}"
            shutil.move(caminho_arquivo, os.path.join(pasta_destino, novo_nome))
            
            print(f"   ✅ Sucesso! Arquivo processado e movido.")

        except Exception as e:
            print(f"   ❌ Erro ao processar {caminho_arquivo}: {e}")

    print("💤 Todos os arquivos processados. Aguardando novos...")

def iniciar():
    schedule.clear()
    try:
        with engine.connect() as conn:
            jobs = conn.execute(text("SELECT nome_job, caminho_arquivo FROM configuracoes_robo WHERE ativo = TRUE")).fetchall()
        
        for job in jobs:
            schedule.every(10).seconds.do(executar_conciliacao, pasta_monitorada=job[1], nome_job=job[0])
            print(f"📅 Agendado: {job[0]} (Monitorando: {job[1]})")
            
    except Exception as e:
        print(f"❌ Erro ao buscar configurações: {e}")

if __name__ == "__main__":
    iniciar()
    while True:
        schedule.run_pending()
        time.sleep(1)