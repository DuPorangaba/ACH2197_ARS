import pandas
import networkx
import numpy
import funcoes_auxiliares
"""
Recomenda ativos com base na analise de grafo (bipartido fundo-ativo)

    Entradas:
    - df_fundos_ativos: matriz que mostra quais ações os fundos possuem
    - cnpj_fundo: o cnpj do fundo alvo
    - top_n: número de recomendações

    Saída:
        Dataframe com as recomendações e pontuação
"""
def recomedacao_baseado_grafo(df_fundos_ativos, cnpj_fundo, top_n=10):
    # Cria o grafo
    G = networkx.Graph()

    # Adiciona os nós
    fundos = df_fundos_ativos['CNPJ_FUNDO_CLASSE'].unique()
    ativos = df_fundos_ativos['CD_ATIVO'].unique()

    G.add_nodes_from(fundos, bipartite=0)
    G.add_nodes_from(ativos, bipartite=1)

    # Adiciona as arestas
    for _, linha in df_fundos_ativos.iterrows():
        # Peso com base na quantidade
        peso = numpy.log1p(linha['VL_MERC_POS_FINAL'])
        G.add_edge(
            linha['CNPJ_FUNDO_CLASSE'],
            linha['CD_ATIVO'],
            weight=peso
        )

    print(f'Grafo Criado: {G.number_of_nodes} nós e {G.number_of_edges} arestas')

    # Checa se o fundo alvo está no Grafo
    if cnpj_fundo not in G:
        print(f"Fundo {cnpj_fundo} não encontrado")
        return pandas.DataFrame()

    # Obtem os ativos atuais do fundo alvo
    ativos_atuais = set(df_fundos_ativos[df_fundos_ativos['CNPJ_FUNDO_CLASSE'] == cnpj_fundo]['CD_ATIVO'])

    # Calcula pontuação PageRank 
    pagerank = networkx.pagerank(G, weight='weight')

    # Alternativa: Usa caminhada aleatória com reinicialização a partir do nó de fundo
    recomendacoes = {}

    # Encontra ações conectadas através de fundos similares
    ativos_do_fundo = list(G.neighbors(cnpj_fundo)) # Ativos do fundo

    for acao in ativos_do_fundo:
        fundos_compartilham_acao = [n for n in G.neighbors(acao) if n in fundos]

        # Para cada fundo similar, guarda seus ativos
        for fundo_similar in fundos_compartilham_acao:
            if fundo_similar != cnpj_fundo:
                for acao_candidata in G.neighbors(fundo_similar):
                    if acao_candidata in ativos and acao_candidata not in ativos_atuais:
                        # Pontuação baseada na força da conexão
                        if acao_candidata not in recomendacoes:
                            recomendacoes[acao_candidata] = {
                                'pontuacao': 0,
                                'contagem_caminhos': 0
                            }
                        
                        peso = (
                            G[cnpj_fundo][acao]['weight'] * G[fundo_similar][acao_candidata]['weight']
                        )

                        recomendacoes[acao_candidata]['pontuacao'] += peso
                        recomendacoes[acao_candidata]['contagem_caminhos'] += 1
        
    for acao in ativos:
        if acao not in ativos_atuais and acao in pagerank:
            if acao not in recomendacoes:
                recomendacoes[acao] = {
                    'pontuacao': 0,
                    'contagem_caminhos': 0
                }
            recomendacoes[acao]['pontuacao'] += pagerank[acao] * 100
    
    if recomendacoes:
        resultados = pandas.DataFrame([
            {
                'ativo': acao,
                'pontuacao': data['pontuacao'],
                'contagem_caminhos': data['contagem_caminhos'],
                'pagerank': pagerank.get(acao, 0)
            }
            for acao, data in recomendacoes.items()
        ]).sort_values('pontuacao', ascending=False).head(top_n)

        resultados = funcoes_auxiliares.adiciona_detalhes_acao(df_fundos_ativos, resultados)
            
        return resultados
        
    return pandas.DataFrame()

    