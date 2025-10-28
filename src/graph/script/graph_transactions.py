import pandas as pd
import networkx as nx
import datetime
import sys
import os

# --- 1. Configurações ---
# ATENÇÃO: Coloque aqui o nome exato do seu arquivo CSV limpo
ARQUIVO_LIMPO = "../../data/output/carteiras_acoes_limpo_202501_20251025_172017.csv" 

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
# As arestas terão pesos de acordo com aquisição e venda do ativo.

# Copiando o grafo
df_graph = df.copy()

print(f"Total de conexões (arestas) a criar: {len(df_graph)}")

# --- 4. Construir o Multigrafo Dirigido (MultiGraph) ---
# As arestas serão de Fundo -> Ativo, com as seguintes caracteristicas:
#   - Valor positivo para aquisição de ativo
#   - Valor negatigo para venda de ativo
print("Construindo o multigrafo dirigido (Fundo -> Ativo)...")
MG = nx.MultiDiGraph()

# Itere sobre o DataFrame de arestas únicas
for i, row in enumerate(df_graph.itertuples(index=False)):
    fund_id = str(row.CNPJ_FUNDO_CLASSE)
    fund_name = row.DENOM_SOCIAL
    asset_id = str(row.CD_ATIVO)
    asset_name = row.DS_ATIVO

    # Adiciona os nós (com o atributo 'type' para diferenciação visual)
    # O Gephi/Kumu usará 'type' para colorir os nós.
    MG.add_node(fund_id, type='fund', name=fund_name)
    MG.add_node(asset_id, type='asset', name=asset_name)

    # MUDANÇA: Adiciona a aresta DIRIGIDA (Fundo -> Ativo) e COM PESO
    if (row.QT_VENDA_NEGOC > 0): MG.add_edge(fund_id, asset_id, key=f"v{i}", weight=row.QT_VENDA_NEGOC, label='venda', color='red')
    if (row.QT_AQUIS_NEGOC > 0): MG.add_edge(fund_id, asset_id, key=f"a{i}",weight=row.QT_AQUIS_NEGOC, label='aquis', color='green') 
    if (row.VL_MERC_POS_FINAL > 0 and row.QT_AQUIS_NEGOC == 0 and row.QT_VENDA_NEGOC == 0): MG.add_edge(fund_id, asset_id, key=f"n{i}",label='na', color='yellow') 

print("Grafo construído com sucesso.")

# --- 5. Estatísticas ---
# (A verificação 'is_bipartite' foi removida, pois não é mais o foco)
    
print("Calculando estatísticas (contando nós por tipo)...")
fund_nodes_count = 0
asset_nodes_count = 0

# Contamos os nós pelo 'type' que definimos
for node, data in MG.nodes(data=True):
    if 'type' in data:
        if data['type'] == 'fund':
            fund_nodes_count += 1
        elif data['type'] == 'asset':
            asset_nodes_count += 1
            
print("\n--- Estatísticas da Rede ---")
print(f"Total de Nós: {MG.number_of_nodes()}")
print(f"  - Nós de Fundos: {fund_nodes_count}")
print(f"  - Nós de Ativos: {asset_nodes_count}")
print(f"Total de Arestas (Conexões): {MG.number_of_edges()}")


# --- 6. Salvar o Grafo ---
try:
    # Garante que o diretório de saída existe
    os.makedirs(os.path.dirname(ARQUIVO_GRAFO_SAIDA), exist_ok=True)
    
    # Salva o novo grafo 'G'
    nx.write_graphml(MG, ARQUIVO_GRAFO_SAIDA)
    print(f"\nGrafo salvo com sucesso em: {ARQUIVO_GRAFO_SAIDA}")
    print("Ao abrir no Gephi, as arestas agora terão setas.")
except Exception as e:
    print(f"\n--- ERRO --- ao salvar o grafo: {e}")