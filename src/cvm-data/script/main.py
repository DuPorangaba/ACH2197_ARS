import pandas as pd
import sys
import datetime
import os # Import 'os' para criar o diretório de saída

# --- 1. Configurações ---
ARQUIVO_ENTRADA = "../input/cda_fi_BLC_4_202501.csv" 

# Cria o diretório de saída (ex: '../output') se ele não existir
os.makedirs('../output', exist_ok=True)

# Gera um timestamp (Data/Hora) para criar nomes de arquivos únicos
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ARQUIVO_SAIDA = f"../output/carteiras_acoes_limpo_202501_{agora}.csv"

# Filtro principal: Manter apenas aplicações do tipo 'Ações'
TIPO_APLICACAO_DESEJADA = 'Ações' 

print(f"Iniciando limpeza do arquivo: {ARQUIVO_ENTRADA}")
print("Este processo pode demorar alguns segundos...")

# --- 2. Carregamento ---
try:
    # Codificação 'latin-1' e separador ';' são padrões dos arquivos da CVM
    # low_memory=False ajuda a evitar erros de tipo em arquivos grandes
    df = pd.read_csv(ARQUIVO_ENTRADA, sep=';', encoding='latin-1', low_memory=False)
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

# --- 3. Limpeza e Conversão de Tipos ---
print("Iniciando conversão de tipos de dados (valores e quantidades)...")

# Lista de colunas de valor (financeiro)
colunas_valor = [
    'VL_MERC_POS_FINAL', 'VL_CUSTO_POS_FINAL', 
    'VL_VENDA_NEGOC', 'VL_AQUIS_NEGOC' 
]
# Lista de colunas de quantidade
colunas_qtd = [
    'QT_POS_FINAL', 
    'QT_VENDA_NEGOC', 'QT_AQUIS_NEGOC'
]

for col in colunas_valor + colunas_qtd:
    if col in df.columns:
        # Garante que a coluna é string antes de usar '.str'
        df[col] = df[col].astype(str) 
        # 1. Remove pontos de milhar (ex: "1.234,56" -> "1234,56")
        df[col] = df[col].str.replace(r'\.', '', regex=True)
        # 2. Troca vírgula de decimal por ponto (ex: "1234,56" -> "1234.56")
        df[col] = df[col].str.replace(',', '.', regex=False)
        # 3. Converte para número. 'coerce' transforma erros de conversão em NaN (Nulo)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    else:
        print(f"Aviso: Coluna esperada '{col}' não encontrada no arquivo.")

# --- 4. Filtragem ---
print("Iniciando filtragem dos dados...")
total_linhas_antes = len(df)

# Filtro 1: Tipo de Aplicação (Mantém apenas linhas onde 'TP_APLIC' == 'Ações')
# (Nota: Este filtro mantém todos os tipos de fundos e todas as datas do mês)
df_filtrado = df[df['TP_APLIC'] == TIPO_APLICACAO_DESEJADA]

# Filtro 2: Remover dados nulos essenciais para a rede
# (Linhas sem CNPJ do fundo ou sem Código do ativo são inúteis para a rede)
df_filtrado = df_filtrado.dropna(subset=['CNPJ_FUNDO_CLASSE', 'CD_ATIVO'])

# --- RECOMENDAÇÃO: Adicionar .copy() ---
# Para evitar o "SettingWithCopyWarning" do Pandas nas próximas etapas
df_filtrado = df_filtrado.copy()

total_linhas_depois = len(df_filtrado)
print(f"Filtragem concluída: {total_linhas_antes} linhas -> {total_linhas_depois} linhas")

# --- 5. Limpeza Adicional (Conforme solicitado) ---

# Limpa a coluna 'CNPJ_FUNDO_CLASSE' para conter apenas números
print("Limpando coluna CNPJ_FUNDO_CLASSE (removendo caracteres especiais)...")
# Usa regex [^0-9] para remover qualquer coisa que NÃO seja um número (pontos, barras, etc.)
df_filtrado['CNPJ_FUNDO_CLASSE'] = df_filtrado['CNPJ_FUNDO_CLASSE'].astype(str).str.replace(r'[^0-9]', '', regex=True)

# --- 6. Seleção de Colunas ---
# Define as colunas finais que queremos no arquivo de saída
colunas_finais = [
    'CNPJ_FUNDO_CLASSE',
    'DENOM_SOCIAL',
    'CD_ATIVO',
    'DS_ATIVO',
    'QT_POS_FINAL',
    'VL_MERC_POS_FINAL',
    'QT_VENDA_NEGOC',
    'VL_VENDA_NEGOC',
    'QT_AQUIS_NEGOC',
    'VL_AQUIS_NEGOC'
]
# Verifica quais colunas da lista realmente existem no DataFrame
colunas_existentes = [col for col in colunas_finais if col in df_filtrado.columns]
# Cria o DataFrame final limpo apenas com as colunas existentes
df_limpo = df_filtrado[colunas_existentes]

# --- 7. Salvar Resultado ---
try:
    # Salva o DataFrame limpo em um novo arquivo CSV
    # 'utf-8-sig' ajuda a manter a acentuação correta ao abrir no Excel
    df_limpo.to_csv(ARQUIVO_SAIDA, index=False, sep=';', encoding='utf-8-sig')
    print(f"\n--- SUCESSO! ---")
    print(f"Dados limpos salvos em: {ARQUIVO_SAIDA}")
    
    print("\n--- 5 primeiras linhas dos dados limpos: ---")
    print(df_limpo.head())
    print("\n----------------------------------------------")
    
except Exception as e:
    print(f"--- ERRO ---")
    print(f"Erro ao salvar o arquivo: {e}")