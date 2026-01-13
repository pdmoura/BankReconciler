import pandas as pd
import pytest
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from main import processar_conciliacao
except ImportError:
    from src.main import processar_conciliacao

def test_conciliacao_sucesso():
    """Testa se valores iguais geram status OK (Caminho Feliz)"""
    # Arrange
    dados_banco = pd.DataFrame({'id_transacao': ['TX01'], 'valor_banco': [100.00]})
    dados_csv = pd.DataFrame({'id_transacao': ['TX01'], 'valor_arquivo': [100.00]})
    
    # Act
    resultado = processar_conciliacao(dados_banco, dados_csv)
    
    # Assert
    assert resultado.iloc[0]['status'] == 'OK'

def test_divergencia_valor():
    """Testa se valores diferentes geram status DIVERGENCIA"""
    dados_banco = pd.DataFrame({'id_transacao': ['TX02'], 'valor_banco': [100.00]})
    dados_csv = pd.DataFrame({'id_transacao': ['TX02'], 'valor_arquivo': [100.01]})
    
    resultado = processar_conciliacao(dados_banco, dados_csv)
    
    assert resultado.iloc[0]['status'] == 'DIVERGENCIA'

def test_falta_no_arquivo():
    """Testa transação que existe no banco mas não no arquivo (Left Only)"""
    dados_banco = pd.DataFrame({'id_transacao': ['TX03'], 'valor_banco': [50.00]})
    dados_csv = pd.DataFrame({'id_transacao': [], 'valor_arquivo': []})
    
    resultado = processar_conciliacao(dados_banco, dados_csv)
    
    assert resultado.iloc[0]['status'] == 'FALTA NO ARQUIVO'

def test_nao_no_banco():
    """Testa transação que existe no arquivo mas não no banco (Right Only)"""
    dados_banco = pd.DataFrame({'id_transacao': [], 'valor_banco': []})
    dados_csv = pd.DataFrame({'id_transacao': ['TX04'], 'valor_arquivo': [75.00]})
    
    resultado = processar_conciliacao(dados_banco, dados_csv)
    
    assert resultado.iloc[0]['status'] == 'NAO NO BANCO'