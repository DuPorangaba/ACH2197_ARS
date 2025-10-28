import pandas as pd
import networkx as nx
import datetime
import sys
import os

# --- 1. Configurações ---
# ATENÇÃO: Coloque aqui o nome exato do seu arquivo CSV limpo
ARQUIVO_LIMPO = "../../data/output/carteiras_acoes_limpo_202501_20251018_164206.csv" 

# MUDANÇA: Novo nome de arquivo para o grafo dirigido
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ARQUIVO_GRAFO_SAIDA = f"../output/rede_dirigida_fundo_ativo_{agora}.graphml"

print(f"Carregando dados limpos de: {ARQUIVO_LIMPO}")

# --- 2. Carregar Dados Limpos ---
try:
    df = pd.read_csv(ARQUIVO_LIMPO, sep=';', encoding='utf-8-sig')
    print("Dados carregados com sucesso.")
except FileNotFoundError:
    print(f"--- ERRO ---")
    print(f"Arquivo '{ARQUIVO_LIMPO}' não encontrado.")
    sys.exit()
except Exception as e:
    print(f"Erro ao carregar o arquivo: {e}")
    sys.exit()

# --- 3. Preparar Arestas (Edges) ---
# Como não queremos pesos, só nos importa se a conexão (Fundo, Ativo) existe.

# MUDANÇA: Filtramos apenas posições que existem (Valor > 0)
# Uma aresta "Fundo -> Ativo" significa que o fundo POSSUI o ativo.
df_graph = df[df['VL_MERC_POS_FINAL'] > 0].copy()

# MUDANÇA: Como seu arquivo de entrada pode ter várias linhas para o mesmo 
# (Fundo, Ativo) em dias diferentes, vamos pegar apenas as conexões únicas.
df_edges = df_graph.drop_duplicates(subset=['CNPJ_FUNDO_CLASSE', 'CD_ATIVO'])

print(f"Total de conexões (arestas) únicas a criar: {len(df_edges)}")


# --- 4. Construir o Grafo Dirigido (DiGraph) ---
print("Construindo o grafo dirigido (Fundo -> Ativo)...")
# MUDANÇA: Criamos um DiGraph (Grafo Dirigido)
G = nx.DiGraph()

# Itere sobre o DataFrame de arestas únicas
for row in df_edges.itertuples(index=False):
    fund_id = str(row.CNPJ_FUNDO_CLASSE)
    fund_name = row.DENOM_SOCIAL
    asset_id = str(row.CD_ATIVO)
    asset_name = row.DS_ATIVO
    
    # Adiciona os nós (com o atributo 'type' para diferenciação visual)
    # O Gephi/Kumu usará 'type' para colorir os nós.
    G.add_node(fund_id, type='fund', name=fund_name)
    G.add_node(asset_id, type='asset', name=asset_name)
    
    # MUDANÇA: Adiciona a aresta DIRIGIDA (Fundo -> Ativo) e SEM PESO
    G.add_edge(fund_id, asset_id) 

print("Grafo construído com sucesso.")

# --- 5. Estatísticas ---
# (A verificação 'is_bipartite' foi removida, pois não é mais o foco)
    
print("Calculando estatísticas (contando nós por tipo)...")
fund_nodes_count = 0
asset_nodes_count = 0

# Contamos os nós pelo 'type' que definimos
for node, data in G.nodes(data=True):
    if 'type' in data:
        if data['type'] == 'fund':
            fund_nodes_count += 1
        elif data['type'] == 'asset':
            asset_nodes_count += 1
            
print("\n--- Estatísticas da Rede ---")
print(f"Total de Nós: {G.number_of_nodes()}")
print(f"  - Nós de Fundos: {fund_nodes_count}")
print(f"  - Nós de Ativos: {asset_nodes_count}")
print(f"Total de Arestas (Conexões): {G.number_of_edges()}")


# --- 6. Salvar o Grafo ---
try:
    # Garante que o diretório de saída existe
    os.makedirs(os.path.dirname(ARQUIVO_GRAFO_SAIDA), exist_ok=True)
    
    # Salva o novo grafo 'G'
    nx.write_graphml(G, ARQUIVO_GRAFO_SAIDA)
    print(f"\nGrafo salvo com sucesso em: {ARQUIVO_GRAFO_SAIDA}")
    print("Ao abrir no Gephi, as arestas agora terão setas.")
except Exception as e:
    print(f"\n--- ERRO --- ao salvar o grafo: {e}")