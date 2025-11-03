import pandas as pd
import sys
import datetime
import os # Import 'os' para criar o diretório de saída

# --- 1. Configurações ---
ARQUIVO_ENTRADA = "../output/carteiras_acoes_limpo_202501_20251101_211535.csv" 

# Cria o diretório de saída (ex: '../output') se ele não existir
os.makedirs('../output', exist_ok=True)

# Gera um timestamp (Data/Hora) para criar nomes de arquivos únicos
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ARQUIVO_SAIDA = f"../output/acoes_limpo_202501_{agora}.csv"

print(f"Iniciando limpeza do arquivo: {ARQUIVO_ENTRADA}")
print("Este processo pode demorar alguns segundos...")

# --- 2. Carregamento ---
try:
    # Codificação 'utf-8-sig' e separador ';' são padrões dos arquivos de saída anteriores
    df = pd.read_csv(ARQUIVO_ENTRADA, sep=';', encoding='utf-8-sig', low_memory=False)
    print("Arquivo carregado com sucesso.")
except FileNotFoundError:
    print(f"--- ERRO ---")
    print(f"Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
    print("Por favor, verifique se o nome do arquivo está correto.")
    sys.exit() # Para o script se o arquivo não for encontrado
except Exception as e:
    print(f"--- ERRO ---")
    print(f"Erro inesperado ao ler o arquivo: {e}")
    sys.exit()

# --- 3. Seleção dos Ativos Existentes ---

# Após criar df_limpo, adicione:
print("\nCriando DataFrame apenas com códigos dos ativos...")

# Cria um novo DataFrame apenas com a coluna CD_ATIVO e remove duplicatas
df_ativos = df[['CD_ATIVO']].drop_duplicates().reset_index(drop=True)

print("\n--- Códigos únicos dos ativos: ---")
print(f"Total de ativos únicos: {len(df_ativos)}")
print("\nPrimeiros 10 ativos:")
print(df_ativos.head(10))

# Salvar lista de ativos em arquivo separado
df_ativos.to_csv('../output/lista_ativos_202501.csv', index=False, sep=';', encoding='utf-8-sig')