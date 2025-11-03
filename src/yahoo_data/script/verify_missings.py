import pandas as pd

df = pd.read_csv("output/carteiras_acoes_infos.csv", sep=";")

count_missing_setor = df["Setor"].isna().sum()
count_missing_industria = df["Industria"].isna().sum()

print(f"Setores faltantes: {count_missing_setor}")
print(f'#'*30)
print(df[df["Setor"].isna()])
print(f"Indústrias faltantes: {count_missing_industria}")
print(f'#'*30)
print(df[df["Industria"].isna()])