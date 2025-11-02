import pandas as pd
import yfinance as yf
from time import sleep

# Lê o CSV de entrada
df = pd.read_csv("../data/output/carteiras_acoes_limpo_202501_20251029_170203.csv", sep=";")

# Pega os códigos únicos
funds = df["CD_ATIVO"].dropna().unique().tolist()

# Cria lista para acumular resultados
dados = []

for fund in funds:
    ticker_symbol = f"{fund}.SA"  # adiciona sufixo da B3
    print(f"Buscando {ticker_symbol}...")

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info or {}

        setor = info.get("sector")
        industria = info.get("industry")

        dados.append({
            "CD_ATIVO": fund,
            "Setor": setor,
            "Industria": industria
        })

    except Exception as e:
        print(f"Erro ao buscar {fund}: {e}")
        dados.append({
            "CD_ATIVO": fund,
            "Setor": None,
            "Industria": None
        })

    sleep(0.5)  # pausa leve para não sobrecarregar o servidor

# Cria DataFrame final
df_funds_infos = pd.DataFrame(dados)

# Salva em CSV
output_path = "output/carteiras_acoes_infos.csv"
df_funds_infos.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")

print(f"\n✅ Arquivo salvo em: {output_path}")