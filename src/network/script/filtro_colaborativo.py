from sklearn.metrics.pairwise import cosine_similarity
import pandas
import funcoes_auxiliares

"""
Filtro colaborativo para recomendação de ações.
Recomenda ações para um fundo com base no que outros fundos semelhantes possuem.
Ou seja, um fundo semelhante é aquele que possui as mesmas ações.
O algoritimo define os fundos que são semelhantes (possuem mesmas ações) e 
recomenda a ação que o fundo não possui, mas os seus semelhantes possuem.
    Entradas:
    - matriz_fundo_acao: matriz que mostra quais ações os fundos possuem
    - cnpj_fundo: o cnpj do fundo alvo
    - top_n: número de recomendações
    - min_similaridade: limite minimo de similaridade

    Saída:
        Dataframe com as recomendações e pontuação
"""

def filtro_colaborativo(df_fundos_ativos, matriz_fundo_acao, cnpj_fundo, top_n=10, min_similaridade=0.1):
    if cnpj_fundo not in matriz_fundo_acao.index:
        print(f"Fundo {cnpj_fundo} não encontrado na matriz!")
        return pandas.DataFrame()

    # Calcula a similaride de cosseno
    matriz_similaridade = cosine_similarity(matriz_fundo_acao)
    df_similaridade = pandas.DataFrame(
        matriz_similaridade,
        index=matriz_fundo_acao.index,
        columns=matriz_fundo_acao.index
    )

    # Seleciona fundos similares
    fundos_similares = df_similaridade[cnpj_fundo].sort_values(ascending=False)
    fundos_similares = fundos_similares[
        (fundos_similares.index != cnpj_fundo) &
        (fundos_similares > min_similaridade)
    ]

    print(f"Foram encontrados {len(fundos_similares)} fundos similares ao {cnpj_fundo}")

    # Obtem os atuais ativos do fundo alvo (fundo_cnpj)
    atuais_ativos = set(
        matriz_fundo_acao.loc[cnpj_fundo][matriz_fundo_acao.loc[cnpj_fundo] > 0].index
    )

    # Calcula a pontuação para os ativos candidatos
    recomendacoes = {}

    for fundo_similar, similaridade in fundos_similares.head(2*top_n).items():
        ativos = matriz_fundo_acao.loc[fundo_similar]
        ativos = ativos[ativos > 0]

        for acao in ativos.index:
            if acao not in atuais_ativos:
                if acao not in recomendacoes:
                    recomendacoes[acao] = 0
                recomendacoes[acao] += similaridade
    
    # Cria DataFrame com os resultados
    if recomendacoes:
        resultados = pandas.DataFrame([
            {
                'ativo': acao,
                'pontuacao': pontuacao,
                'quantidade_fundos_similares': sum(
                    1 for fundo in fundos_similares.head(2*top_n).index
                    if matriz_fundo_acao.loc[fundo, acao] > 0
                )
            }
            for acao, pontuacao in recomendacoes.items()
        ]).sort_values('pontuacao', ascending=False).head(top_n)

        # Adiciona os detalhes do ativo 
        resultados_com_detalhes = funcoes_auxiliares.adiciona_detalhes_acao(df_fundos_ativos, resultados)

        return resultados_com_detalhes
    
    return pandas.DataFrame()