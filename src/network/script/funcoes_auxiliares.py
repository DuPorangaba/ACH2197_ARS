"""Adiciona o nome e setor do ativo no DataFrame de resultados"""
def adiciona_detalhes_acao(df_fundo_ativos, resultados):   
    if len(resultados) > 0 and 'ativo' in resultados.columns:
        stock_info = df_fundo_ativos[['CD_ATIVO', 'DS_ATIVO', 'Setor']].drop_duplicates()
        stock_info.columns = ['ativo', 'nome', 'setor']
        resultados = resultados.merge(stock_info, on='ativo', how='left')
    return resultados

"""Obtem o perfil do fundo"""
def obtem_perfil_fundo(df_fundos_ativos, cnpj_fundo):
    dados_fundo = df_fundos_ativos[
        df_fundos_ativos['CNPJ_FUNDO_CLASSE'] == cnpj_fundo
    ]
    
    if len(dados_fundo) == 0:
        print(f"Fund {cnpj_fundo} not found!")
        return
    
    print(f"\n{'='*60}")
    print(f"Perfil do fundo: {dados_fundo['DENOM_SOCIAL'].iloc[0][:60]}")
    print(f"{'='*60}")
    
    print(f"\nTotal de ativos: {len(dados_fundo)}")
    print(f"Total valor de mercado: R$ {dados_fundo['VL_MERC_POS_FINAL'].sum():,.2f}")
    
    print(f"\nDistribuição dos setores:")
    dist_setor = dados_fundo.groupby('Setor')['VL_MERC_POS_FINAL'].sum()
    dist_setor = dist_setor.sort_values(ascending=False)
    for sector, value in dist_setor.items():
        pct = value / dist_setor.sum() * 100
        print(f"  {sector:30s}: {pct:5.1f}%")
    
    print(f"\nTop 10 ativos:")
    top_ativos = dados_fundo.nlargest(10, 'VL_MERC_POS_FINAL')
    for _, linha in top_ativos.iterrows():
        pct = linha['VL_MERC_POS_FINAL'] / dados_fundo['VL_MERC_POS_FINAL'].sum() * 100
        print(f"  {linha['CD_ATIVO']:8s} - {linha['DS_ATIVO'][:40]:40s}: {pct:5.1f}%")


