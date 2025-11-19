import filtro_colaborativo
import filtro_conteudo
import filtro_grafo_compra_venda
import pandas
import funcoes_auxiliares

"""
Combina todas as abordagens

    Entradas:
    - cnpj_fundo:
        - cnpj_fundo: o cnpj do fundo alvo
    - top_n: número de recomendações

    Saída:
        Dataframe com as recomendações e pontuação
"""

def filtro_hibrido(df_fundo_ativos, matriz_fundos_ativos, cnpj_fundo, top_n=10):
    # Recomedacoes para cada abordagem
    rec_colaborativo = filtro_colaborativo.filtro_colaborativo(df_fundo_ativos, matriz_fundos_ativos, cnpj_fundo, top_n=20)
    rec_conteudo = filtro_conteudo.filtro_baseado_conteudo(df_fundo_ativos, cnpj_fundo, top_n=20)
    rec_grafo = filtro_grafo_compra_venda.recomendacao_baseada_em_grafo_compra_venda(df_fundo_ativos ,cnpj_fundo, top_n=20)

    # Normalizando a pontuacao
    def normaliza_pontuacao(df):
        if len(df) > 0 and 'pontuacao' in df.columns:
            df = df.copy()
            max_pontuacao = df['pontuacao'].max()
            if max_pontuacao > 0:
                df['pontuacao'] = df['pontuacao'] / max_pontuacao
        return df

    rec_colaborativo = normaliza_pontuacao(rec_colaborativo)
    rec_conteudo = normaliza_pontuacao(rec_conteudo)
    rec_grafo = normaliza_pontuacao(rec_grafo)

    # Combina as recomendações
    todos_ativos = set()
    if len(rec_colaborativo) > 0:
        todos_ativos.update(rec_colaborativo['ativo'])
    if len(rec_conteudo) > 0:
        todos_ativos.update(rec_conteudo['ativo'])
    if len(rec_grafo) > 0:
        todos_ativos.update(rec_grafo['ativo'])
    
    # Calcula os pesos com as pontuações combinadas
    resultados_combinados = []

    for acao in todos_ativos:
        pontuacoes = {}

        if len(rec_colaborativo) > 0:
            pontuacao_colaborativo = rec_colaborativo[rec_colaborativo['ativo'] == acao]['pontuacao'].values
            pontuacoes['colaborativo'] = pontuacao_colaborativo[0] if len(pontuacao_colaborativo) > 0 else 0
        else:
            pontuacoes['colaborativo'] = 0
            
        if len(rec_conteudo) > 0:
            pontuacao_conteudo = rec_conteudo[rec_conteudo['ativo'] == acao]['pontuacao'].values
            pontuacoes['conteudo'] = pontuacao_conteudo[0] if len(pontuacao_conteudo) > 0 else 0
        else:
            pontuacoes['conteudo'] = 0
            
        if len(rec_grafo) > 0:
            pontuacao_grafo = rec_grafo[rec_grafo['ativo'] == acao]['pontuacao'].values
            pontuacoes['grafo'] = pontuacao_grafo[0] if len(pontuacao_grafo) > 0 else 0
        else:
            pontuacoes['grafo'] = 0

        # Combinação utilizando pesos
        pontuacao_combinada = (
            0.3 * pontuacoes['colaborativo'] +
            0.3 * pontuacoes['conteudo'] +
            0.3 * pontuacoes['grafo']
        )

        resultados_combinados.append({
            'ativo': acao,
            'pontuacao_combinada': pontuacao_combinada,
            'pontuacao_colaborativo': pontuacoes['colaborativo'],
            'pontuacao_conteudo': pontuacoes['conteudo'],
            'pontuacao_grafo': pontuacoes['grafo'],
            'num_metodos': sum(1 for s in pontuacoes.values() if s > 0)
        })
    
    resultados = pandas.DataFrame(resultados_combinados)
    resultados = resultados.sort_values('pontuacao_combinada', ascending=False).head(top_n)

    # Adiciona os detalhes das ações
    resultados = funcoes_auxiliares.adiciona_detalhes_acao(df_fundo_ativos ,resultados)
        
    return resultados