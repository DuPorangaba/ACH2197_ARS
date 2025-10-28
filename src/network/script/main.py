import pandas as pd
import json
import sys
import os
import datetime

# --- Classes de Modelo ---

class Fundo:
    """Representa um único fundo de investimento."""
    def __init__(self, fundo_id, nome):
        self.id = fundo_id
        self.nome = nome
        # Dicionário para armazenar os ativos e seus detalhes
        # Chave: ID do Ativo, Valor: Dicionário com detalhes da posição
        self.ativos = {}

    def adicionar_ativo(self, ativo_id, detalhes_posicao):
        """Adiciona uma conexão com um ativo e seus detalhes."""
        self.ativos[ativo_id] = detalhes_posicao

    def to_dict(self):
        """Converte o objeto Fundo para um dicionário serializável."""
        return {
            "id": self.id,
            "nome": self.nome,
            "total_conexoes_ativos": len(self.ativos),
            "ativos": self.ativos
        }

class Ativo:
    """Representa uma única ação (ativo)."""
    def __init__(self, ativo_id, nome):
        self.id = ativo_id
        self.nome = nome
        # Usamos um set para garantir que os IDs dos fundos sejam únicos
        self._fundos_investidores_set = set()

    def adicionar_fundo(self, fundo_id):
        """Adiciona uma conexão com um fundo que investe neste ativo."""
        self._fundos_investidores_set.add(fundo_id)

    def to_dict(self):
        """Converte o objeto Ativo para um dicionário serializável."""
        # Convertendo o set para uma lista para a saída JSON
        fundos_investidores_lista = sorted(list(self._fundos_investidores_set))
        return {
            "id": self.id,
            "nome": self.nome,
            "total_conexoes_fundos": len(fundos_investidores_lista),
            "fundos_investidores": fundos_investidores_lista
        }

# --- Classe de Processamento ---

class ProcessadorDeRede:
    """
    Lê os dados limpos, cria os objetos de Fundo e Ativo
    e gera os arquivos JSON de saída.
    """
    def __init__(self, arquivo_entrada):
        self.arquivo_entrada = arquivo_entrada
        # Dicionários para acesso rápido aos objetos já criados
        self.fundos = {}
        self.ativos = {}

    def processar(self):
        """Método principal para executar todo o processo."""
        print(f"Carregando dados de: {self.arquivo_entrada}")
        try:
            df = pd.read_csv(self.arquivo_entrada, sep=';', encoding='utf-8-sig')
            # Converte CNPJ para string para evitar problemas com notação científica
            df['CNPJ_FUNDO_CLASSE'] = df['CNPJ_FUNDO_CLASSE'].astype(str)
        except FileNotFoundError:
            print(f"--- ERRO ---: Arquivo '{self.arquivo_entrada}' não encontrado.")
            sys.exit()
        except Exception as e:
            print(f"--- ERRO --- ao ler o arquivo: {e}")
            sys.exit()

        print("Dados carregados. Processando e criando objetos...")
        
        # Itera sobre cada linha do DataFrame para construir os objetos
        for row in df.itertuples(index=False):
            fundo_id = row.CNPJ_FUNDO_CLASSE
            ativo_id = row.CD_ATIVO
            
            # --- Cria ou obtém o objeto Fundo ---
            if fundo_id not in self.fundos:
                self.fundos[fundo_id] = Fundo(fundo_id=fundo_id, nome=row.DENOM_SOCIAL)
            
            fundo_obj = self.fundos[fundo_id]
            
            # --- Cria ou obtém o objeto Ativo ---
            if ativo_id not in self.ativos:
                self.ativos[ativo_id] = Ativo(ativo_id=ativo_id, nome=row.DS_ATIVO)
                
            ativo_obj = self.ativos[ativo_id]
            
            # --- Constrói as relações ---
            detalhes_posicao = {
                'QT_POS_FINAL': row.QT_POS_FINAL,
                'VL_MERC_POS_FINAL': row.VL_MERC_POS_FINAL,
                'QT_VENDA_NEGOC': row.QT_VENDA_NEGOC,
                'VL_VENDA_NEGOC': row.VL_VENDA_NEGOC,
                'QT_AQUIS_NEGOC': row.QT_AQUIS_NEGOC,
                'VL_AQUIS_NEGOC': row.VL_AQUIS_NEGOC
            }
            
            # Adiciona a conexão no objeto Fundo
            fundo_obj.adicionar_ativo(ativo_id, detalhes_posicao)
            
            # Adiciona a conexão no objeto Ativo
            ativo_obj.adicionar_fundo(fundo_id)
            
        print("Processamento concluído.")
        
    def salvar_json(self, pasta_saida):
        """Salva os dados processados em dois arquivos JSON."""
        print("Preparando para salvar os arquivos JSON...")
        os.makedirs(pasta_saida, exist_ok=True)
        
        # --- Prepara dados dos Fundos ---
        lista_fundos_dict = [fundo.to_dict() for fundo in self.fundos.values()]
        output_fundos = {
            "quantidade_total_fundos": len(lista_fundos_dict),
            "fundos": lista_fundos_dict
        }
        
        # --- Prepara dados dos Ativos ---
        lista_ativos_dict = [ativo.to_dict() for ativo in self.ativos.values()]
        output_ativos = {
            "quantidade_total_ativos": len(lista_ativos_dict),
            "ativos": lista_ativos_dict
        }

        # --- Salva os arquivos ---
        agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_fundos = os.path.join(pasta_saida, f'fundos_{agora}.json')
        caminho_ativos = os.path.join(pasta_saida, f'ativos_{agora}.json')

        try:
            with open(caminho_fundos, 'w', encoding='utf-8') as f:
                # indent=2 para o arquivo ficar legível
                json.dump(output_fundos, f, ensure_ascii=False, indent=2)
            print(f"Arquivo de fundos salvo em: {caminho_fundos}")
            
            with open(caminho_ativos, 'w', encoding='utf-8') as f:
                json.dump(output_ativos, f, ensure_ascii=False, indent=2)
            print(f"Arquivo de ativos salvo em: {caminho_ativos}")

        except Exception as e:
            print(f"--- ERRO --- ao salvar arquivos JSON: {e}")


# --- Execução Principal ---
if __name__ == "__main__":
    # --- Configurações ---
    # ATENÇÃO: Coloque aqui o nome exato do seu arquivo CSV limpo
    ARQUIVO_ENTRADA_LIMPO = "../../data/output/carteiras_acoes_limpo_202501_20251018_164206.csv"
    agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    PASTA_SAIDA_JSON = f"../output/json/{agora}/"

    # Cria e executa o processador
    processador = ProcessadorDeRede(ARQUIVO_ENTRADA_LIMPO)
    processador.processar()
    processador.salvar_json(PASTA_SAIDA_JSON)

    print("\n--- SUCESSO! --- Script concluído.")