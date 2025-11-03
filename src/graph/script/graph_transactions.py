import pandas as pd
import networkx as nx
import datetime
import sys
import os
from typing import Tuple, Optional, Dict

def setup_paths(periodo: str) -> Tuple[str, str]:
    """Setup input and output file paths."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    arquivo_limpo = os.path.join(base_dir, "output", f"carteiras_com_setores_{periodo}.csv")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.join(base_dir, "graph", "output"), exist_ok=True)
    
    # Generate output filename
    arquivo_grafo = os.path.join(base_dir, "graph", "output", f"rede_dirigida_fundo_ativo_{periodo}.graphml")
    
    return arquivo_limpo, arquivo_grafo

def load_data(arquivo_limpo: str) -> Optional[pd.DataFrame]:
    """Load and validate input data."""
    try:
        df = pd.read_csv(arquivo_limpo, sep=';', encoding='utf-8-sig')
        print("Dados carregados com sucesso.")
        return df
    except FileNotFoundError:
        print(f"--- ERRO --- Arquivo '{arquivo_limpo}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o arquivo: {e}")
        return None

def build_multigraph(df: pd.DataFrame) -> nx.MultiDiGraph:
    """Build directed multigraph from data."""
    print("Construindo o multigrafo dirigido (Fundo -> Ativo)...")
    MG = nx.MultiDiGraph()
    
    for i, row in enumerate(df.itertuples(index=False)):
        fund_id = str(row.CNPJ_FUNDO_CLASSE)
        fund_name = row.DENOM_SOCIAL
        asset_id = str(row.CD_ATIVO)
        asset_name = row.DS_ATIVO
        
        MG.add_node(fund_id, type='fund', name=fund_name, node_size=5)
        MG.add_node(asset_id, type='asset', name=asset_name, node_size=10)
        
        if row.QT_VENDA_NEGOC > 0:
            MG.add_edge(fund_id, asset_id, key=f"v{i}", 
                       weight=row.QT_VENDA_NEGOC, label='venda', color='red')
        if row.QT_AQUIS_NEGOC > 0:
            MG.add_edge(fund_id, asset_id, key=f"a{i}",
                       weight=row.QT_AQUIS_NEGOC, label='aquis', color='green')
    
    return MG

def calculate_statistics(MG: nx.MultiDiGraph) -> Dict[str, int]:
    """Calculate graph statistics."""
    stats = {'fund': 0, 'asset': 0, 'sector': 0}
    
    for _, data in MG.nodes(data=True):
        if 'type' in data:
            stats[data['type']] = stats.get(data['type'], 0) + 1
    
    stats['total_nodes'] = MG.number_of_nodes()
    stats['total_edges'] = MG.number_of_edges()
    
    return stats

def save_graph(MG: nx.MultiDiGraph, arquivo_grafo: str) -> bool:
    """Save graph to file."""
    try:
        os.makedirs(os.path.dirname(arquivo_grafo), exist_ok=True)
        nx.write_graphml(MG, arquivo_grafo)
        print(f"\nGrafo salvo com sucesso em: {arquivo_grafo}")
        return True
    except Exception as e:
        print(f"\n--- ERRO --- ao salvar o grafo: {e}")
        return False

def create_transaction_graph(periodo: str) -> Optional[nx.MultiDiGraph]:
    """Main function to create and process the transaction graph."""
    # Setup paths
    arquivo_limpo, arquivo_grafo = setup_paths(periodo)
    print(f"Carregando dados limpos de: {arquivo_limpo}")
    
    # Load data
    df = load_data(arquivo_limpo)
    if df is None:
        return None
    
    # Build multigraph
    MG = build_multigraph(df)
    
    # Calculate and print statistics
    stats = calculate_statistics(MG)
    print("\n--- Estatísticas da Rede ---")
    print(f"Total de Nós: {stats['total_nodes']}")
    print(f"  - Nós de Fundos: {stats['fund']}")
    print(f"  - Nós de Ativos: {stats['asset']}")
    print(f"  - Nós de Setores: {stats['sector']}")
    print(f"Total de Arestas (Conexões): {stats['total_edges']}")
    
    # Save graph
    if save_graph(MG, arquivo_grafo):
        return MG
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python graph_transactions.py PERIOD")
        print("Example: python graph_transactions.py 202501")
        sys.exit(1)
    
    periodo = sys.argv[1]
    create_transaction_graph(periodo)