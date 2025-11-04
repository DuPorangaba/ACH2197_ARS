import pandas as pd
import yfinance as yf
from time import sleep
import os
from typing import List, Dict
import datetime

def setup_paths(periodo: str) -> tuple:
    """Configura os caminhos de entrada e saída."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    input_path = os.path.join(base_dir, "cvm_data", "output", f"carteiras_acoes_limpo_{periodo}.csv")
        
    # Cria o diretório de saída se não existir
    os.makedirs(os.path.join(base_dir, "yahoo_data", "output"), exist_ok=True)

    # Gera nome do arquivo de saída
    output_path = os.path.join(base_dir, "yahoo_data", "output", f"ativo_setores-{periodo}.csv")

    return input_path, output_path

def load_data(input_path: str) -> List[str]:
    """Carrega dados e retorna códigos únicos dos fundos."""
    try:
        df = pd.read_csv(input_path, sep=";")
        return df["CD_ATIVO"].dropna().unique().tolist()
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return []

def fetch_yahoo_data(fund: str) -> Dict:
    """Busca dados do Yahoo Finance para um único fundo."""
    ticker_symbol = f"{fund}.SA"
    print(f"Buscando {ticker_symbol}...")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info or {}
        
        return {
            "CD_ATIVO": fund,
            "Setor": info.get("sector"),
            "Industria": info.get("industry")
        }
    except Exception as e:
        print(f"Erro ao buscar {fund}: {e}")
        return {
            "CD_ATIVO": fund,
            "Setor": None,
            "Industria": None
        }

def process_funds(funds: List[str]) -> pd.DataFrame:
    """Processa todos os fundos e retorna DataFrame consolidado."""
    dados = []
    for fund in funds:
        dados.append(fetch_yahoo_data(fund))
        sleep(0.5)  # evita sobrecarregar o servidor
    
    return pd.DataFrame(dados)

def save_results(df: pd.DataFrame, output_path: str) -> None:
    """Salva resultados em arquivo CSV."""
    try:
        df.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
        print(f"\n Arquivo salvo em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

def yahoo_data(periodo: str) -> pd.DataFrame:
    """Função principal para processar dados do Yahoo Finance."""
    # Configura caminhos
    input_path, output_path = setup_paths(periodo)
    
    # Carrega códigos únicos dos fundos
    funds = load_data(input_path)
    if not funds:
        return pd.DataFrame()
    
    # Processa fundos
    df_funds_infos = process_funds(funds)
    
    # Salva resultados
    save_results(df_funds_infos, output_path)
    
    return df_funds_infos

if __name__ == "__main__":
    # Se executando como script principal, usa argumento de linha de comando para período
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python main.py PERIODO")
        print("Exemplo: python main.py 202501")
        sys.exit(1)
    
    periodo = sys.argv[1]
    yahoo_data(periodo)