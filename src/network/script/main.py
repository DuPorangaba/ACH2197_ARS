import pandas as pd
import sys
import os
from typing import Dict

import filtro_grafo
import filtro_grafo_compra_venda
import filtro_colaborativo
import filtro_conteudo
import filtro_hibrido
import funcoes_auxiliares

class SistemaRecomendadorAcoes:
    """
    Sistema Abrangente de Recomendação de Ações implementando múltiplas abordagens:
    1. Filtragem Colaborativa (similaridade baseada em fundos)
    2. Filtragem por Conteúdo (baseada em setor/atributos)
    3. Análise de Co-ocorrência (cesta de mercado)
    4. Abordagem baseada em Grafo (análise de rede)
    """
    
    def __init__(self, caminho_csv: str):
        """
        Inicializa o sistema de recomendação com dados.
        
        Args:
            caminho_csv: Caminho para o arquivo CSV com dados de carteiras
        """
        self.df = pd.read_csv(caminho_csv, sep=',', encoding='utf-8-sig')
        self._preprocessar_dados()
        
    def _preprocessar_dados(self):
        """Limpa e prepara os dados."""
        # Converte colunas numéricas
        colunas_numericas = ['QT_POS_FINAL', 'VL_MERC_POS_FINAL', 
                            'QT_VENDA_NEGOC', 'VL_VENDA_NEGOC',
                            'QT_AQUIS_NEGOC', 'VL_AQUIS_NEGOC']
        
        for col in colunas_numericas:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Filtra apenas posições com saldo
        self.df_fundos_ativos = self.df[self.df['QT_POS_FINAL'] > 0].copy()

        # Converte CNPJ para string
        self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'] = self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'].astype("string")
        
        # Cria matriz fundo-ação
        self.matriz_fundo_acao = self.df_fundos_ativos.pivot_table(
            index='CNPJ_FUNDO_CLASSE',
            columns='CD_ATIVO',
            values='VL_MERC_POS_FINAL',
            fill_value=0
        )
        
        print(f"✅ Dados carregados: {len(self.df_fundos_ativos)} posições")
        print(f"📊 Fundos únicos: {self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'].nunique()}")
        print(f"📈 Ações únicas: {self.df_fundos_ativos['CD_ATIVO'].nunique()}")
    
    def obter_perfil_fundo(self, cnpj_fundo: str) -> Dict:
        funcoes_auxiliares.obtem_perfil_fundo(self.df_fundos_ativos, cnpj_fundo)
    
    def recomendar_filtragem_colaborativa(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando filtragem colaborativa.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por filtragem colaborativa...")
        resultados = filtro_colaborativo.filtro_colaborativo(
            self.df_fundos_ativos, 
            self.matriz_fundo_acao, 
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def recomendar_filtragem_conteudo(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando filtragem por conteúdo.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por filtragem de conteúdo...")
        resultados = filtro_conteudo.filtro_baseado_conteudo(
            self.df_fundos_ativos, 
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def recomendar_analise_grafo(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando análise de grafo/rede.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por análise de grafo...")
        resultados = filtro_grafo_compra_venda.recomendacao_baseada_em_grafo_compra_venda(
            self.df_fundos_ativos, 
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def recomendar_filtro_hibrido(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando filtro híbrido (combinação de todas as abordagens).
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por filtro híbrido...")
        resultados = filtro_hibrido.filtro_hibrido(
            self.df_fundos_ativos, 
            self.matriz_fundo_acao,
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def comparar_abordagens(self, cnpj_fundo: str, top_n: int = 10) -> Dict[str, pd.DataFrame]:
        """
        Compara todas as abordagens de recomendação.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            Dicionário com resultados de cada abordagem
        """
        print("\n" + "="*60)
        print("GERANDO RECOMENDAÇÕES PARA O FUNDO")
        print("="*60)
        
        resultados = {
            'filtragem_colaborativa': self.recomendar_filtragem_colaborativa(cnpj_fundo, top_n),
            'filtragem_conteudo': self.recomendar_filtragem_conteudo(cnpj_fundo, top_n),
            'analise_grafo': self.recomendar_analise_grafo(cnpj_fundo, top_n),
            'hibrido': self.recomendar_filtro_hibrido(cnpj_fundo, top_n)
        }
        return resultados
    
    def salvar_recomendacoes(self, resultados: Dict[str, pd.DataFrame], diretorio_saida: str = '../saida') -> None:
        """
        Salva as recomendações em arquivos CSV.
        
        Args:
            resultados: Dicionário com resultados de cada abordagem
            diretorio_saida: Diretório de saída
        """
        os.makedirs(diretorio_saida, exist_ok=True)
        
        for abordagem, df in resultados.items():
            caminho_saida = os.path.join(diretorio_saida, f"recomendacoes_{abordagem}.csv")
            df.to_csv(caminho_saida, sep=';', encoding='utf-8-sig', index=False)
            print(f"✅ Recomendações {abordagem} salvas em: {caminho_saida}")

# ==================== EXEMPLO DE USO ====================

if __name__ == "__main__":
    # Inicializa o sistema de recomendação
    print("📂 Carregando Sistema de Recomendação de Ações...")
    ARQUIVO_ENTRADA = '../../output/carteiras_com_setores_202406_amostra.csv'
    sistema = SistemaRecomendadorAcoes(ARQUIVO_ENTRADA)
    
    # Seleciona um fundo para análise
    # Usaremos um dos maiores fundos
    cnpj_fundo_alvo = '2661252000197'  # FAPI AGGRESSIVE IB MULTIMERCADO
    
    # Obtém perfil do fundo
    sistema.obter_perfil_fundo(cnpj_fundo_alvo)
    
    # Aplica cada abordagem de recomendação
    print(f"\n\n{'#'*60}")
    print("GERANDO RECOMENDAÇÕES PARA O FUNDO")
    print(f"{'#'*60}")
    
    # 1. Filtragem Colaborativa
    print("\n--- FILTRAGEM COLABORATIVA ---")
    recomendacoes_colaborativo = sistema.recomendar_filtragem_colaborativa(cnpj_fundo_alvo, top_n=10)
    print(recomendacoes_colaborativo.head(10))
    
    # 2. Filtragem por Conteúdo
    print("\n--- FILTRAGEM POR CONTEÚDO ---")
    recomendacoes_conteudo = sistema.recomendar_filtragem_conteudo(cnpj_fundo_alvo, top_n=10)
    print(recomendacoes_conteudo.head(10))

    # 3. Análise de Grafo
    print("\n--- ANÁLISE DE GRAFO ---")
    recomendacoes_grafo = sistema.recomendar_analise_grafo(cnpj_fundo_alvo, top_n=10)
    print(recomendacoes_grafo[['ativo', 'nome', 'setor', 'pontuacao', 
        'contagem_compras', 'contagem_vendas', 'proporcao_compra']].head(10))
    
    # 4. Filtro Híbrido
    print("\n--- FILTRO HÍBRIDO ---")
    recomendacoes_hibrido = sistema.recomendar_filtro_hibrido(cnpj_fundo_alvo, top_n=15)
    print(recomendacoes_hibrido.head(15))
    
    print(f"\n{'='*60}")
    print("SISTEMA DE RECOMENDAÇÃO FINALIZADO")
    print(f"{'='*60}")