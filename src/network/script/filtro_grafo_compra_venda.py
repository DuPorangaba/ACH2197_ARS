import pandas
import networkx
import numpy
import funcoes_auxiliares

"""
Recomenda ativos com base em análise de grafo com sinais de compra e venda
    
    Cria uma rede direcionada com pesos positivos/negativos onde:
    - Arestas POSITIVAS: Compras (QT_AQUIS_NEGOC > 0) = Sinal de alta (bullish)
    - Arestas NEGATIVAS: Vendas (QT_VENDA_NEGOC > 0) = Sinal de baixa (bearish)
    
    Lógica: Se fundos similares estão COMPRANDO uma ação (sentimento positivo),
            recomenda. Se estão VENDENDO, evita.
    
    Entradas:
    - df_fundos_ativos: DataFrame completo com dados de negociação
    - cnpj_fundo: CNPJ do fundo alvo
    - top_n: Número de recomendações
    
    Saída:
    - DataFrame com ativos recomendados e pontuações
"""
def recomendacao_baseada_em_grafo_compra_venda(df_fundos_ativos, cnpj_fundo, top_n=10):
    
    print(f"\n{'='*60}")
    print("RECOMENDAÇÃO POR GRAFO: Análise de Sinais de Compra/Venda")
    print(f"{'='*60}")
    
    # Cria grafo DIRECIONADO com pesos com sinal (positivo/negativo)
    G = networkx.DiGraph()
    
    # Adiciona os nós
    fundos = df_fundos_ativos['CNPJ_FUNDO_CLASSE'].unique().astype('str')
    ativos = df_fundos_ativos['CD_ATIVO'].unique().astype('str')
    
    G.add_nodes_from(fundos, bipartite=0, tipo_no='fundo')
    G.add_nodes_from(ativos, bipartite=1, tipo_no='ativo')
    
    # Rastreia estatísticas de sentimento
    sinais_compra = 0
    sinais_venda = 0
    sinais_neutros = 0
    
    # Adiciona arestas baseadas em atividade de compra/venda
    for _, linha in df_fundos_ativos.iterrows():
        fundo = linha['CNPJ_FUNDO_CLASSE']
        ativo = linha['CD_ATIVO']
        
        qtd_comprada = linha['QT_AQUIS_NEGOC']
        qtd_vendida = linha['QT_VENDA_NEGOC']
        val_comprado = linha['VL_AQUIS_NEGOC']
        val_vendido = linha['VL_VENDA_NEGOC']
        
        # Calcula sentimento líquido
        # Positivo = comprando, Negativo = vendendo
        quantidade_liquida = qtd_comprada - qtd_vendida
        valor_liquido = val_comprado - val_vendido
        
        if valor_liquido != 0:  # Houve atividade de negociação
            # Cria aresta com peso com sinal
            # Peso positivo = alta (comprando)
            # Peso negativo = baixa (vendendo)
            
            # Usa transformação logarítmica para normalizar valores grandes
            if valor_liquido > 0:
                peso = numpy.log1p(abs(valor_liquido))
                sentimento = 'compra'
                sinais_compra += 1
            else:
                peso = -numpy.log1p(abs(valor_liquido))
                sentimento = 'venda'
                sinais_venda += 1
            
            G.add_edge(
                fundo,
                ativo,
                weight=peso,
                sentimento=sentimento,
                valor_liquido=valor_liquido,
                quantidade_liquida=quantidade_liquida
            )
        elif linha['QT_POS_FINAL'] > 0:
            # Mantendo mas sem atividade = neutro
            sinais_neutros += 1
    
    print(f"Grafo criado: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    print(f"Sinais de compra (arestas positivas): {sinais_compra}")
    print(f"Sinais de venda (arestas negativas): {sinais_venda}")
    print(f"Posições sem atividade: {sinais_neutros}")
    
    # Obtém posições e atividade atuais do fundo
    dados_fundo = df_fundos_ativos[df_fundos_ativos['CNPJ_FUNDO_CLASSE'] == cnpj_fundo]
    
    if len(dados_fundo) == 0 or cnpj_fundo not in G:
        print(f"Fundo {cnpj_fundo} não encontrado!")
        return pandas.DataFrame()
    
    # Obtém ativos atualmente mantidos pelo fundo
    ativos_atuais = set(dados_fundo[
        dados_fundo['QT_POS_FINAL'] > 0
    ]['CD_ATIVO'])
    
    print(f"\nAnalisando padrões de negociação de {len(ativos_atuais)} ativos mantidos")
    
    # Calcula pontuações de sentimento dos ativos
    recomendacoes = {}
    
    # Método 1: Agregação direta de sentimento
    # Para cada ativo, agrega sentimento de todos os fundos
    for ativo in ativos:
        if ativo not in ativos_atuais:
            # Obtém todas as arestas que apontam para este ativo
            arestas_entrada = G.in_edges(ativo, data=True)
            
            sentimento_total = 0
            contagem_compras = 0
            contagem_vendas = 0
            volume_total = 0
            
            for fundo, _, dados_aresta in arestas_entrada:
                peso = dados_aresta['weight']
                sentimento_total += peso
                volume_total += abs(dados_aresta['valor_liquido'])
                
                if dados_aresta['sentimento'] == 'compra':
                    contagem_compras += 1
                else:
                    contagem_vendas += 1
            
            # Calcula métricas
            if contagem_compras + contagem_vendas > 0:
                proporcao_compra = contagem_compras / (contagem_compras + contagem_vendas)
                
                recomendacoes[ativo] = {
                    'pontuacao_sentimento': sentimento_total,
                    'contagem_compras': contagem_compras,
                    'contagem_vendas': contagem_vendas,
                    'proporcao_compra': proporcao_compra,
                    'sinal_liquido': contagem_compras - contagem_vendas,
                    'volume_total': volume_total,
                    'pontuacao_atividade': contagem_compras + contagem_vendas
                }
    
    # Método 2: Análise de fundos similares
    # Encontra fundos similares ao fundo alvo baseado em posições sobrepostas
    similaridade_fundos = {}
    
    for outro_fundo in fundos:
        if outro_fundo != cnpj_fundo:
            # Calcula similaridade de Jaccard baseada em ativos mantidos
            outras_posicoes = set(df_fundos_ativos[
                (df_fundos_ativos['CNPJ_FUNDO_CLASSE'] == outro_fundo) &
                (df_fundos_ativos['QT_POS_FINAL'] > 0)
            ]['CD_ATIVO'])
            
            if len(outras_posicoes) > 0:
                intersecao = len(ativos_atuais & outras_posicoes)
                uniao = len(ativos_atuais | outras_posicoes)
                similaridade = intersecao / uniao if uniao > 0 else 0
                
                if similaridade > 0.05:  # Pelo menos 5% de sobreposição
                    similaridade_fundos[outro_fundo] = similaridade
    
    print(f"Encontrados {len(similaridade_fundos)} fundos similares")
    
    # Método 3: Recomendações ponderadas de fundos similares
    for ativo in recomendacoes.keys():
        sentimento_ponderado = 0
        
        # Obtém sentimento de fundos similares
        for fundo_similar, similaridade in similaridade_fundos.items():
            if G.has_edge(fundo_similar, ativo):
                dados_aresta = G[fundo_similar][ativo]
                # Pondera pela similaridade do fundo
                sentimento_ponderado += dados_aresta['weight'] * similaridade
        
        recomendacoes[ativo]['sentimento_ponderado'] = sentimento_ponderado
    
    # Calcula pontuação final combinando múltiplos fatores
    for ativo in recomendacoes.keys():
        rec = recomendacoes[ativo]
        
        # Normaliza componentes
        max_atividade = max([r['pontuacao_atividade'] for r in recomendacoes.values()]) or 1
        
        # Pontuação final combina:
        # 1. Sentimento geral do mercado (40%)
        # 2. Sentimento de fundos similares (30%)
        # 3. Proporção de compra (20%)
        # 4. Nível de atividade de negociação (10%)
        
        pontuacao = (
            0.40 * rec['pontuacao_sentimento'] +
            0.30 * rec['sentimento_ponderado'] +
            0.20 * rec['proporcao_compra'] * 10 +  # Escala para faixa comparável
            0.10 * (rec['pontuacao_atividade'] / max_atividade) * 10
        )
        
        recomendacoes[ativo]['pontuacao_final'] = pontuacao
    
    # Cria DataFrame de resultados
    if recomendacoes:
        resultados = pandas.DataFrame([
            {
                'ativo': ativo,
                'pontuacao': dados['pontuacao_final'],
                'pontuacao_sentimento': dados['pontuacao_sentimento'],
                'contagem_compras': dados['contagem_compras'],
                'contagem_vendas': dados['contagem_vendas'],
                'proporcao_compra': dados['proporcao_compra'],
                'sinal_liquido': dados['sinal_liquido'],
                'sentimento_ponderado': dados['sentimento_ponderado']
            }
            for ativo, dados in recomendacoes.items()
        ])
        
        # Filtra apenas sentimento positivo
        resultados = resultados[resultados['pontuacao'] > 0].sort_values(
            'pontuacao', ascending=False
        ).head(top_n)
        
        # Adiciona detalhes do ativo
        resultados = funcoes_auxiliares.adiciona_detalhes_acao(df_fundos_ativos, resultados)
        
        if len(resultados) <= 0:
            print("Nenhum ativo com sentimento líquido positivo encontrado.")
        
        return resultados
    
    return pandas.DataFrame()
