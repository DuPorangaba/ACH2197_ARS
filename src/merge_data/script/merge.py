import pandas as pd
import sys
import datetime
import os
from typing import Tuple

def setup_paths(periodo: str) -> Tuple[str, str, str]:
    """Configura os caminhos dos arquivos de entrada e saída."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    carteiras_path = os.path.join(base_dir, "cvm_data", "output", f"carteiras_acoes_limpo_{periodo}.csv")
    setores_path = os.path.join(base_dir, "yahoo_data", "output", f"ativo_setores-{periodo}.csv")

    # Cria o diretório de saída
    os.makedirs(os.path.join(base_dir, "output"), exist_ok=True)

    # Gera nome do arquivo de saída
    output_path = os.path.join(base_dir, "output", f"carteiras_com_setores_{periodo}.csv")

    return carteiras_path, setores_path, output_path

def load_dataframes(carteiras_path: str, setores_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega ambos os DataFrames de entrada."""
    try:
        df_carteiras = pd.read_csv(carteiras_path, sep=';', encoding='utf-8-sig')
        print("Arquivo de carteiras carregado com sucesso.")
        
        df_setores = pd.read_csv(setores_path, sep=';', encoding='utf-8-sig')
        print("Arquivo de setores carregado com sucesso.")
        
        return df_carteiras, df_setores
    except FileNotFoundError as e:
        print(f"ERRO: Arquivo não encontrado - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO: Erro inesperado ao ler arquivos - {e}")
        sys.exit(1)

def merge_dataframes(df_carteiras: pd.DataFrame, df_setores: pd.DataFrame) -> pd.DataFrame:
    """Une os DataFrames de carteiras e setores e remove registros sem setor."""
    try:
        df_merged = pd.merge(
            df_carteiras,
            df_setores[['CD_ATIVO', 'Setor']],
            on='CD_ATIVO',
            how='left'
        )
        
        # Imprime estatísticas antes de remover setores nulos
        print("\nEstatísticas antes da remoção de registros sem setor:")
        print(f"Total de registros: {len(df_merged)}")
        print(f"Registros sem setor: {df_merged['Setor'].isna().sum()}")
        
        # Remove registros onde Setor é nulo
        df_merged = df_merged.dropna(subset=['Setor'])
        
        # Reordena as colunas para colocar 'Setor' como quarta coluna
        colunas = list(df_merged.columns)
        colunas.remove('Setor')
        colunas.insert(3, 'Setor')
        df_merged = df_merged[colunas]
        
        print("\nEstatísticas após remoção de registros sem setor:")
        print_merge_stats(df_carteiras, df_merged)
        return df_merged
    except Exception as e:
        print(f"ERRO: Falha ao realizar merge - {e}")
        sys.exit(1)

def print_merge_stats(df_carteiras: pd.DataFrame, df_merged: pd.DataFrame) -> None:
    """Imprime estatísticas do merge."""
    print(f"\nMerge concluído:")
    print(f"Registros originais: {len(df_carteiras)}")
    print(f"Registros após merge: {len(df_merged)}")
    sem_setor = df_merged['Setor'].isna().sum()
    print(f"Registros sem setor: {sem_setor}")

def save_results(df_merged: pd.DataFrame, output_path: str) -> None:
    """Salva o DataFrame unido em CSV."""
    try:
        df_merged.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
        print(f"\nArquivo salvo com sucesso em: {output_path}")
        print("\nPrimeiras 5 linhas do resultado:")
        print(df_merged.head())
    except Exception as e:
        print(f"ERRO: Falha ao salvar arquivo - {e}")
        sys.exit(1)

def merge_data(periodo: str) -> pd.DataFrame:
    """Função principal para unir dados de carteiras e setores."""
    print("Iniciando processo de merge dos arquivos...")
    
    # Configura caminhos
    carteiras_path, setores_path, output_path = setup_paths(periodo)
    
    # Carrega dados
    df_carteiras, df_setores = load_dataframes(carteiras_path, setores_path)
    
    # Une dataframes
    df_merged = merge_dataframes(df_carteiras, df_setores)
    
    # Salva resultados
    save_results(df_merged, output_path)
    
    return df_merged

if __name__ == "__main__":
    # Se executando como script principal, usa argumento de linha de comando para período
    if len(sys.argv) != 2:
        print("Uso: python merge.py PERIODO")
        print("Exemplo: python merge.py 202501")
        sys.exit(1)
    
    periodo = sys.argv[1]
    merge_data(periodo)