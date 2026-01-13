import pandas as pd
import pytest


def calcular_conciliacao(df_banco, df_csv):
    # Simula o Merge
    df_final = pd.merge(df_banco, df_csv, on='id_transacao', how='outer', indicator=True)
    
    # Simula a Regra de Negócio
    def classificar(row):
        if row['_merge'] == 'left_only': return 'FALTA NO ARQUIVO'
        if row['_merge'] == 'right_only': return 'NAO NO BANCO'
        if row['valor_banco'] != row['valor_arquivo']: return 'DIVERGENCIA VALOR'
        return 'CONCILIADO'

    df_final['status'] = df_final.apply(classificar, axis=1)
    return df_final

def test_conciliacao_sucesso():
    """Testa se valores iguais geram status CONCILIADO"""
    dados_banco = pd.DataFrame({'id_transacao': ['TX01'], 'valor_banco': [100.00]})
    dados_csv = pd.DataFrame({'id_transacao': ['TX01'], 'valor_arquivo': [100.00]})
    
    resultado = calcular_conciliacao(dados_banco, dados_csv)
    assert resultado.iloc[0]['status'] == 'CONCILIADO'

def test_divergencia_valor():
    """Testa se valores diferentes geram status DIVERGENCIA VALOR"""
    dados_banco = pd.DataFrame({'id_transacao': ['TX02'], 'valor_banco': [100.00]})
    dados_csv = pd.DataFrame({'id_transacao': ['TX02'], 'valor_arquivo': [100.01]})
    
    resultado = calcular_conciliacao(dados_banco, dados_csv)
    assert resultado.iloc[0]['status'] == 'DIVERGENCIA VALOR'

def test_falta_no_arquivo():
    """Testa transação que existe no banco mas não no arquivo"""
    dados_banco = pd.DataFrame({'id_transacao': ['TX03'], 'valor_banco': [50.00]})
    dados_csv = pd.DataFrame({'id_transacao': [], 'valor_arquivo': []})
    
    resultado = calcular_conciliacao(dados_banco, dados_csv)
    assert resultado.iloc[0]['status'] == 'FALTA NO ARQUIVO'