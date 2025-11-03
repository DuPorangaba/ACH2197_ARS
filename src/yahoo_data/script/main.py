import pandas as pd
import yfinance as yf
from time import sleep
import os
from typing import List, Dict
import datetime

def setup_paths(periodo: str) -> tuple:
    """Setup input and output paths."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    input_path = os.path.join(base_dir, "cvm_data", "output", f"carteiras_acoes_limpo_{periodo}.csv")
        
    # Create output directory if it doesn't exist
    os.makedirs(os.path.join(base_dir, "yahoo_data", "output"), exist_ok=True)

    # Generate output filename with timestamp
    output_path = os.path.join(base_dir, "yahoo_data", "output", f"ativo_setores-{periodo}.csv")

    return input_path, output_path

def load_data(input_path: str) -> List[str]:
    """Load input data and return unique fund codes."""
    try:
        df = pd.read_csv(input_path, sep=";")
        return df["CD_ATIVO"].dropna().unique().tolist()
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return []

def fetch_yahoo_data(fund: str) -> Dict:
    """Fetch data from Yahoo Finance for a single fund."""
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
    """Process all funds and return consolidated DataFrame."""
    dados = []
    for fund in funds:
        dados.append(fetch_yahoo_data(fund))
        sleep(0.5)  # avoid overloading the server
    
    return pd.DataFrame(dados)

def save_results(df: pd.DataFrame, output_path: str) -> None:
    """Save results to CSV file."""
    try:
        df.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
        print(f"\n Arquivo salvo em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

def yahoo_data(periodo: str) -> pd.DataFrame:
    """Main function to process Yahoo Finance data."""
    # Setup paths
    input_path, output_path = setup_paths(periodo)
    
    # Load unique fund codes
    funds = load_data(input_path)
    if not funds:
        return pd.DataFrame()
    
    # Process funds
    df_funds_infos = process_funds(funds)
    
    # Save results
    save_results(df_funds_infos, output_path)
    
    return df_funds_infos

if __name__ == "__main__":
    # If running as main script, use command line argument for period
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python main.py PERIOD")
        print("Example: python main.py 202501")
        sys.exit(1)
    
    periodo = sys.argv[1]
    yahoo_data(periodo)