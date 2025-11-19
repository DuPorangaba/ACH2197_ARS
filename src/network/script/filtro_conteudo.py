import pandas
"""
Filtro baseado em conteúdo para recomendação de ações.
Recomenda ativos com base na preferência de setor do fundo e
popularidade do ativo (quantos fundos possuem o ativo)

    Entradas:
    - df_fundos_ativos: matriz que mostra quais ações os fundos possuem
    - cnpj_fundo: o cnpj do fundo alvo
    - top_n: número de recomendações

    Saída:
        Dataframe com as recomendações e pontuação
"""

def filtro_baseado_conteudo(df_fundos_ativos, cnpj_fundo, top_n=10):

    # Ativos do fundo alvo
    fundo_alvo_ativos = df_fundos_ativos[df_fundos_ativos['CNPJ_FUNDO_CLASSE'] == cnpj_fundo].copy()

    # Checa se o fundo existe
    if len(fundo_alvo_ativos) == 0:
        print(f'Fundo {cnpj_fundo} não encontrado.')
        return pandas.DataFrame()
    
    # Calcula a distribuição dos setores
    pesos_setores = fundo_alvo_ativos.groupby('Setor')['VL_MERC_POS_FINAL'].sum()
    pesos_setores = pesos_setores / pesos_setores.sum()

    print(f"\nPerfil do Fundo com base nos setores:")
    for setor, peso in pesos_setores.items():
        print(f'   {setor}: {peso:.1%}')

    # Ativos que o fundo ainda não possui
    ativos_atuais = set(fundo_alvo_ativos['CD_ATIVO'])
    ativos_candidatos = df_fundos_ativos[~df_fundos_ativos['CD_ATIVO'].isin(ativos_atuais)].copy()

    # Calcula a pontuação com base no setor
    ativos_candidatos['pontuacao_setor'] = ativos_candidatos['Setor'].map(pesos_setores).fillna(0)

    # Calcula popularidade do ativo (quantos fundos possuem o ativo)
    ativo_popularidade = df_fundos_ativos.groupby('CD_ATIVO').size()
    ativos_candidatos['popularidade'] = ativos_candidatos['CD_ATIVO'].map(ativo_popularidade)

    # Normalização e combina as pontuações (distribuição dos setores e popularidade)
    max_popularidade = ativos_candidatos['popularidade'].max()
    ativos_candidatos['popularidade_norm'] = (ativos_candidatos['popularidade'] / max_popularidade)

    ativos_candidatos['pontuacao'] = (
        0.7 * ativos_candidatos['pontuacao_setor'] +
        0.3 * ativos_candidatos['popularidade_norm']
    )

    # Seleciona as top_n recomedações
    resultados = ativos_candidatos.groupby('CD_ATIVO').agg({
        'DS_ATIVO': 'first',
        'Setor': 'first',
        'pontuacao': 'max',
        'popularidade': 'first'
    }).reset_index()

    resultados.columns = ['ativo', 'nome', 'setor', 'pontuacao', 'popularidade']
    resultados = resultados.sort_values('pontuacao', ascending=False).head(top_n)

    return resultados