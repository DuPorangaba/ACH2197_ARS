import pandas as pd
import sys
import datetime
import os

# --- 1. Configurações ---
ARQUIVO_CARTEIRAS = "../../cvm-data/output/carteiras_acoes_limpo_202501_20251101_211535.csv"
ARQUIVO_SETORES = "../../yahoo-data/output/ativo_setores-01_2025.csv"

# Cria o diretório de saída se não existir
os.makedirs('../output', exist_ok=True)

# Gera timestamp para nome do arquivo
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ARQUIVO_SAIDA = f"../output/carteiras_com_setores_{agora}.csv"

print("Iniciando processo de merge dos arquivos...")

# --- 2. Carregamento dos arquivos ---
try:
    # Carrega arquivo de carteiras
    df_carteiras = pd.read_csv(ARQUIVO_CARTEIRAS, sep=';', encoding='utf-8-sig')
    print("Arquivo de carteiras carregado com sucesso.")
    
    # Carrega arquivo de setores
    df_setores = pd.read_csv(ARQUIVO_SETORES, sep=';', encoding='utf-8-sig')
    print("Arquivo de setores carregado com sucesso.")
    
except FileNotFoundError as e:
    print(f"ERRO: Arquivo não encontrado - {e}")
    sys.exit()
except Exception as e:
    print(f"ERRO: Erro inesperado ao ler arquivos - {e}")
    sys.exit()


# --- 3. Merge dos DataFrames ---
try:
    # Realiza o merge usando CD_ATIVO como chave
    df_merged = pd.merge(
        df_carteiras,
        df_setores[['CD_ATIVO', 'Setor']],
        on='CD_ATIVO',
        how='left'
    )
    print(df_merged.head())
    
    # Reordena as colunas para colocar 'setor' como quarta coluna
    colunas = list(df_merged.columns)
    colunas.remove('Setor')
    colunas.insert(3, 'Setor')  # Insere 'Setor' na posição 3 (quarta coluna)
    df_merged = df_merged[colunas]
    
    print(f"\nMerge concluído:")
    print(f"Registros originais: {len(df_carteiras)}")
    print(f"Registros após merge: {len(df_merged)}")
    
    # Verifica registros sem setor
    sem_setor = df_merged['Setor'].isna().sum()
    print(f"Registros sem setor: {sem_setor}")
    
except Exception as e:
    print(f"ERRO: Falha ao realizar merge - {e}")
    sys.exit()

# --- 4. Salvar resultado ---
try:
    df_merged.to_csv(ARQUIVO_SAIDA, index=False, sep=';', encoding='utf-8-sig')
    print(f"\nArquivo salvo com sucesso em: {ARQUIVO_SAIDA}")
    
    print("\nPrimeiras 5 linhas do resultado:")
    print(df_merged.head())
    
except Exception as e:
    print(f"ERRO: Falha ao salvar arquivo - {e}")
    sys.exit()