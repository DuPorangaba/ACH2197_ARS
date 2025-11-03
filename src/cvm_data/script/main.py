import pandas as pd
import sys
import datetime
import os # Import 'os' para criar o diretório de saída

# --- 1. Configurações ---
def cvm_data_limpeza(arquivo_entrada):
    # --- 1. Configurações ---
    ARQUIVO_ENTRADA = arquivo_entrada   

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    # Cria o diretório de saída
    os.makedirs(os.path.join(base_dir, "cvm_data", "output"), exist_ok=True)

    # Extrai o número do período do nome do arquivo
    import re
    numero_arquivo = re.search(r'_(\d+)\.', arquivo_entrada)
    numero_periodo = numero_arquivo.group(1) if numero_arquivo else "000000"

    # Gera nome do arquivo de saída
    ARQUIVO_SAIDA = os.path.join(base_dir, "cvm_data", "output", f"carteiras_acoes_limpo_{numero_periodo}.csv")

    # Define tipo de aplicação
    TIPO_APLICACAO_DESEJADA = 'Ações' 

    print(f"Iniciando limpeza do arquivo: {ARQUIVO_ENTRADA}")
    print("Este processo pode demorar alguns segundos...")

    # --- 2. Carregamento ---
    df = carregar_arquivo(ARQUIVO_ENTRADA)
    if df is None:
        return

    # --- 3. Limpeza e Conversão ---
    df_convertido = limpar_e_converter(df)

    # --- 4. Filtragem ---
    df_filtrado = filtrar_dados(df_convertido, TIPO_APLICACAO_DESEJADA)

    # --- 5. Limpeza Adicional ---
    df_limpo = limpeza_adicional(df_filtrado)

    # --- 6. Seleção de Colunas ---
    df_final = selecionar_colunas(df_limpo)

    # --- 7. Salvar Resultado ---
    salvar_arquivo(df_final, ARQUIVO_SAIDA)

    return df_final


# --- 2. Carregamento ---
def carregar_arquivo(ARQUIVO_ENTRADA):
    try:
        # Codificação 'latin-1' e separador ';' são padrões dos arquivos da CVM
        # low_memory=False ajuda a evitar erros de tipo em arquivos grandes
        df = pd.read_csv(ARQUIVO_ENTRADA, sep=';', encoding='latin-1', low_memory=False)
        print("Arquivo carregado com sucesso.")
        return df
    except Exception as e:
        print(f"--- ERRO ---")
        print(f"Erro inesperado ao ler o arquivo: {e}")
        sys.exit()
    except FileNotFoundError:
        print(f"--- ERRO ---")
        print(f"Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
        print("Por favor, verifique se o nome do arquivo está correto.")
        sys.exit() # Para o script se o arquivo não for encontrado
    except Exception as e:
        print(f"--- ERRO ---")
        print(f"Erro inesperado ao ler o arquivo: {e}")
        sys.exit()
    return df 

# --- 3. Limpeza e Conversão de Tipos ---
def limpar_e_converter(df):
    print("Iniciando conversão de tipos de dados (valores e quantidades)...")
    df_limpo_convertido = df.copy()
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
        if col in df_limpo_convertido.columns:
            # Garante que a coluna é string antes de usar '.str'
            df_limpo_convertido[col] = df_limpo_convertido[col].astype(str) 
            # 1. Remove pontos de milhar (ex: "1.234,56" -> "1234,56")
            df_limpo_convertido[col] = df_limpo_convertido[col].str.replace(r'\.', '', regex=True)
            # 2. Troca vírgula de decimal por ponto (ex: "1234,56" -> "1234.56")
            df_limpo_convertido[col] = df_limpo_convertido[col].str.replace(',', '.', regex=False)
            # 3. Converte para número. 'coerce' transforma erros de conversão em NaN (Nulo)
            df_limpo_convertido[col] = pd.to_numeric(df_limpo_convertido[col], errors='coerce')
        else:
            print(f"Aviso: Coluna esperada '{col}' não encontrada no arquivo.")

    return df_limpo_convertido

# --- 4. Filtragem ---
def filtrar_dados(df, TIPO_APLICACAO_DESEJADA):
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
    return df_filtrado

# --- 5. Limpeza Adicional (Conforme solicitado) ---
def limpeza_adicional(df_filtrado):
    print("Iniciando limpeza adicional dos dados...")

    # Limpa a coluna 'CNPJ_FUNDO_CLASSE' para conter apenas números
    print("Limpando coluna CNPJ_FUNDO_CLASSE (removendo caracteres especiais)...")
    # Usa regex [^0-9] para remover qualquer coisa que NÃO seja um número (pontos, barras, etc.)
    df_filtrado['CNPJ_FUNDO_CLASSE'] = df_filtrado['CNPJ_FUNDO_CLASSE'].astype(str).str.replace(r'[^0-9]', '', regex=True)
    return df_filtrado

# --- 6. Seleção de Colunas ---
def selecionar_colunas(df_filtrado):
    print("Selecionando colunas finais para o arquivo de saída...")
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
    return df_limpo

# --- 7. Salvar Resultado ---
def salvar_arquivo(df_limpo, ARQUIVO_SAIDA):
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