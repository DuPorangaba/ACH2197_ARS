import csv
import datetime
import os

# --- 1. Configurações ---
ARQUIVO_ENTRADA = "../input/COTAHIST_M012025.TXT"

# Cria o diretório de saída (ex: '../output') se ele não existir
os.makedirs('../output', exist_ok=True)

# Gera um timestamp (Data/Hora) para criar nomes de arquivos únicos
agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ARQUIVO_SAIDA = f"../output/cotacoes_historicas_202501_{agora}.csv"

print(f"Iniciando formatacao do arquivo: {ARQUIVO_ENTRADA}")
print("Este processo pode demorar alguns segundos...")

# --- 2. Formatacao do Arquivo ---

# Definindo o cabecalho
def parse_header(line):
    """Parse registro tipo 00 (Header)"""
    return {
        'tipo_registro': line[0:2],
        'nome_arquivo': line[2:15].strip(),
        'codigo_origem': line[15:23].strip(),
        'data_geracao': line[23:31]
    }

# Definindo as cotacoes
def parse_cotacao(line):
    """Parse registro tipo 01 (Cotações)"""
    return {
        'tipo_registro': line[0:2],
        'data_pregao': line[2:10],
        'codbdi': line[10:12],
        'codneg': line[12:24].strip(),
        'tpmerc': line[24:27],
        'nomres': line[27:39].strip(),
        'especi': line[39:49].strip(),
        'prazot': line[49:52].strip(),
        'modref': line[52:56].strip(),
        'preabe': float(line[56:69]) / 100,
        'premax': float(line[69:82]) / 100,
        'premin': float(line[82:95]) / 100,
        'premed': float(line[95:108]) / 100,
        'preult': float(line[108:121]) / 100,
        'preofc': float(line[121:134]) / 100,
        'preofv': float(line[134:147]) / 100,
        'totneg': int(line[147:152]),
        'quatot': int(line[152:170]),
        'voltot': float(line[170:188]) / 100,
        'preexe': float(line[188:201]) / 100,
        'indopc': line[201:202],
        'datven': line[202:210],
        'fatcot': int(line[210:217]),
        'ptoexe': float(line[217:230]) / 1000000,
        'codisi': line[230:242].strip(),
        'dismes': line[242:245]
    }


def parse_trailer(line):
    """Parse registro tipo 99 (Trailer)"""
    return {
        'tipo_registro': line[0:2],
        'nome_arquivo': line[2:15].strip(),
        'codigo_origem': line[15:23].strip(),
        'data_geracao': line[23:31],
        'total_registros': int(line[31:42])
    }

# Covertendo a data para DD/MM/AAAA
def format_date(date_str):
    """Converte data AAAAMMDD para DD/MM/AAAA"""
    if len(date_str) == 8:
        return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
    return date_str

# --- 3. Converte txt em csv ---
def convert_cotahist_to_csv(input_file, output_file):
    """Converte arquivo COTAHIST para CSV"""
    
    cotacoes = []
    header_info = None
    trailer_info = None
    
    # Ler arquivo de entrada
    with open(input_file, 'r', encoding='latin-1') as f:
        for line in f:
            tipo = line[0:2]
            
            if tipo == '00':
                header_info = parse_header(line)
                print(f"Arquivo: {header_info['nome_arquivo']}")
                print(f"Origem: {header_info['codigo_origem']}")
                print(f"Data Geração: {format_date(header_info['data_geracao'])}")
                
            elif tipo == '01':
                cotacao = parse_cotacao(line)
                cotacao['data_pregao'] = format_date(cotacao['data_pregao'])
                if cotacao['datven'] and len(cotacao['datven']) == 8:
                    cotacao['datven'] = format_date(cotacao['datven'])
                cotacoes.append(cotacao)
                
            elif tipo == '99':
                trailer_info = parse_trailer(line)
                print(f"Total de registros: {trailer_info['total_registros']}")
    
    # Escrever arquivo CSV
    if cotacoes:
        fieldnames = cotacoes[0].keys()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(cotacoes)
        
        print(f"\nArquivo CSV gerado com sucesso: {output_file}")
        print(f"Total de cotações convertidas: {len(cotacoes)}")
    else:
        print("Nenhuma cotação encontrada no arquivo.")


if __name__ == "__main__":
    try:
        convert_cotahist_to_csv(ARQUIVO_ENTRADA, ARQUIVO_SAIDA)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
