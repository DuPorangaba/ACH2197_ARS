import pandas as pd
import networkx as nx
import datetime
import sys
import os
from typing import Tuple, Optional

def setup_paths(periodo: str) -> Tuple[str, str]:
    """Setup input and output file paths."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    arquivo_limpo = os.path.join(base_dir, "output", f"carteiras_com_setores_{periodo}.csv")
    
    # Create output directory if it doesn't exist
    os.makedirs('graph/output/', exist_ok=True)
    
    # Generate output filename
    arquivo_grafo = f"graph/output/rede_dirigida_fundo_setor_{periodo}.graphml"

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

def prepare_edges(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare edges data for graph construction."""
    df_graph = df[df['VL_MERC_POS_FINAL'] > 0].copy()
    df_edges = df_graph.drop_duplicates(subset=['CNPJ_FUNDO_CLASSE', 'CD_ATIVO'])
    print(f"Total de conexões (arestas) únicas a criar: {len(df_edges)}")
    return df_edges

def build_graph(df_edges: pd.DataFrame) -> nx.DiGraph:
    """Build directed graph from edges data."""
    print("Construindo o grafo dirigido (Fundo -> Ativo)...")
    G = nx.DiGraph()

    for i, row in enumerate(df_edges.itertuples(index=False)):
        fund_id = str(row.CNPJ_FUNDO_CLASSE)
        fund_name = row.DENOM_SOCIAL
        setor = row.Setor

        G.add_node(setor, type='sector', name=setor, node_size=5)
        G.add_node(fund_id, type='fund', name=fund_name)
        
        if row.QT_VENDA_NEGOC > 0:
            G.add_edge(fund_id, setor, key=f"v{i}", 
                       weight=row.QT_VENDA_NEGOC, label='venda', color='red')
        if row.QT_AQUIS_NEGOC > 0:
            G.add_edge(fund_id, setor, key=f"a{i}",
                       weight=row.QT_AQUIS_NEGOC, label='aquis', color='green')
    
    return G

def calculate_statistics(G: nx.DiGraph) -> dict:
    """Calculate graph statistics."""
    print("Calculando estatísticas (contando nós por tipo)...")
    fund_nodes = sum(1 for _, data in G.nodes(data=True) if data.get('type') == 'fund')
    asset_nodes = sum(1 for _, data in G.nodes(data=True) if data.get('type') == 'asset')
    
    stats = {
        'total_nodes': G.number_of_nodes(),
        'fund_nodes': fund_nodes,
        'asset_nodes': asset_nodes,
        'total_edges': G.number_of_edges()
    }
    
    return stats

def save_graph(G: nx.DiGraph, arquivo_grafo: str) -> bool:
    """Save graph to file."""
    try:
        os.makedirs(os.path.dirname(arquivo_grafo), exist_ok=True)
        nx.write_graphml(G, arquivo_grafo)
        print(f"\nGrafo salvo com sucesso em: {arquivo_grafo}")
        return True
    except Exception as e:
        print(f"\n--- ERRO --- ao salvar o grafo: {e}")
        return False

def create_graph(periodo: str) -> Optional[nx.DiGraph]:
    """Main function to create and process the graph."""
    # Setup paths
    arquivo_limpo, arquivo_grafo = setup_paths(periodo)
    print(f"Carregando dados limpos de: {arquivo_limpo}")
    
    # Load data
    df = load_data(arquivo_limpo)
    if df is None:
        return None
    
    # Process data
    df_edges = prepare_edges(df)
    G = build_graph(df_edges)
    
    # Calculate and print statistics
    stats = calculate_statistics(G)
    print("\n--- Estatísticas da Rede ---")
    print(f"Total de Nós: {stats['total_nodes']}")
    print(f"  - Nós de Fundos: {stats['fund_nodes']}")
    print(f"  - Nós de Ativos: {stats['asset_nodes']}")
    print(f"Total de Arestas (Conexões): {stats['total_edges']}")
    
    # Save graph
    if save_graph(G, arquivo_grafo):
        return G
    return None

if __name__ == "__main__":
    create_graph()