"""Tuntum seção a seção: calibra o voto da Bruna na cidade-base.

Referências observadas na própria cidade:
- grupo Pessoa: Fernando (prefeito 2024) -> Eric (dep. estadual 2022, candidato de fora) = conversão ~66%
- grupo Tema:   Tema (prefeito 2024)     -> Cleomar Tema (dep. estadual 2022, candidato local) = ~83%
A Bruna é candidata local do grupo Pessoa: faixa entre as duas conversões.

Entradas: VOTACAO_PREFEITO.csv e SEÇÕES.xlsx (campanha 2024) + seções TSE 2018/2022.
Saídas: tuntum_secoes_v13.csv, tuntum_bairros_v13.csv, tuntum_resumo_v13.json
"""
import json
import re
from pathlib import Path

import pandas as pd

ORIGEM = Path("C:/Users/umled/OneDrive/Documentos/VOTACAO VEREADOR")
TSE = Path(__file__).resolve().parent.parent / "dados_tse"
NUM = {"eric": 55800, "cleomar_tema": 19000, "fernando_dep_2018": 77800, "daniella_2018": 25456}


def secao_principal(texto):
    return int(re.search(r"\d+", str(texto)).group())


pref = pd.read_csv(ORIGEM / "VOTACAO_PREFEITO.csv", sep=";", encoding="latin1")
pref.columns = ["secao_txt", "fernando_2024", "tema_2024"]
sec = pd.read_excel(ORIGEM / "SEÇÕES.xlsx")
sec.columns = sec.columns.str.strip()
sec = sec.rename(columns={"SEÇÃO": "secao_txt", "LOCAL DE VOTAÇÃO": "local", "BAIRRO": "bairro",
                          "Eleitores aptos": "aptos_2024", "Comparecimento": "comparecimento_2024"})
sec["secao_txt"] = sec["secao_txt"].astype(str).str.strip()
pref["secao_txt"] = pref["secao_txt"].astype(str).str.strip()
t = pref.merge(sec[["secao_txt", "local", "bairro", "aptos_2024", "comparecimento_2024"]], on="secao_txt", how="left")
t["bairro"] = (t["bairro"].astype(str).str.strip().str.upper()
               .replace({"IPU IRU": "IPU-IRU", "BELEM": "BELÉM"}))
t["secao"] = t["secao_txt"].map(secao_principal)

for ano, chaves in [(2022, ["eric", "cleomar_tema"]), (2018, ["fernando_dep_2018", "daniella_2018"])]:
    d = pd.read_csv(TSE / f"tuntum_secao_{ano}_dep_est.csv")
    for k in chaves:
        s = d[d.NR_VOTAVEL == NUM[k]].groupby("NR_SECAO").QT_VOTOS.sum()
        t[k] = t["secao"].map(s).fillna(0).astype(int)

CONV = {"conservador": t.eric.sum() / t.fernando_2024.sum(),       # padrão candidato de fora
        "forte": t.cleomar_tema.sum() / t.tema_2024.sum()}         # padrão candidato local
CONV["realista"] = (CONV["conservador"] + CONV["forte"]) / 2
for k, v in CONV.items():
    t[f"bruna_{k}"] = (t.fernando_2024 * v).round()
# eleitor do grupo que em 2022 não seguiu a indicação: alvo do corpo a corpo
t["grupo_nao_convertido_2022"] = (t.fernando_2024 - t.eric).clip(lower=0)
t["margem_fernando_2024"] = t.fernando_2024 - t.tema_2024
t.to_csv("tuntum_secoes_v13.csv", index=False, encoding="utf-8")

bairros = (t.groupby("bairro")
           .agg(secoes=("secao", "count"), aptos_2024=("aptos_2024", "sum"),
                fernando_2024=("fernando_2024", "sum"), tema_2024=("tema_2024", "sum"),
                eric_2022=("eric", "sum"), cleomar_tema_2022=("cleomar_tema", "sum"),
                bruna_conservador=("bruna_conservador", "sum"), bruna_realista=("bruna_realista", "sum"),
                bruna_forte=("bruna_forte", "sum"), grupo_nao_convertido_2022=("grupo_nao_convertido_2022", "sum"))
           .reset_index().sort_values("bruna_realista", ascending=False))
bairros["pct_fernando_2024"] = (100 * bairros.fernando_2024 / (bairros.fernando_2024 + bairros.tema_2024)).round(1)
bairros.to_csv("tuntum_bairros_v13.csv", index=False, encoding="utf-8")

resumo = {
    "secoes": int(len(t)), "fernando_2024": int(t.fernando_2024.sum()), "tema_2024": int(t.tema_2024.sum()),
    "eric_2022": int(t.eric.sum()), "cleomar_tema_2022": int(t.cleomar_tema.sum()),
    "conversao": {k: round(float(v), 3) for k, v in CONV.items()},
    "bruna": {k: int(t[f"bruna_{k}"].sum()) for k in CONV},
    "grupo_nao_convertido_2022": int(t.grupo_nao_convertido_2022.sum()),
}
json.dump(resumo, open("tuntum_resumo_v13.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(resumo, ensure_ascii=False, indent=1))
print(bairros.to_string(index=False))
print("seções sem cadastro de bairro:", t.bairro.isin(["NAN"]).sum())
