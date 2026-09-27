"""Reconstrói a distribuição das 42 cadeiras de deputado estadual (MA 2022)
pela regra do quociente eleitoral (Lei 14.211/2021) e mede a "linha de corte".

Saída: corte_2022.json e eleitos_2022_simulado.csv
"""
import json
import math

import pandas as pd

VAGAS = 42
FEDERACOES = {13: "FE BRASIL", 65: "FE BRASIL", 43: "FE BRASIL",
              45: "FE PSDB/CIDADANIA", 23: "FE PSDB/CIDADANIA",
              50: "FE PSOL/REDE", 18: "FE PSOL/REDE"}

v = pd.read_csv("../dados_tse/votos_2022_municipio.csv")
v = v[(v.DS_CARGO == "Deputado Estadual") & (~v.NR_VOTAVEL.isin([95, 96]))]
v = v.groupby(["NR_VOTAVEL", "NM_VOTAVEL"], as_index=False).QT_VOTOS.sum()
v["partido"] = v.NR_VOTAVEL.astype(str).str[:2].astype(int)
v["grupo"] = v.partido.map(lambda p: FEDERACOES.get(p, str(p)))
v["nominal"] = v.NR_VOTAVEL >= 100

validos = int(v.QT_VOTOS.sum())
qe = math.floor(validos / VAGAS + 0.5)
grupos = v.groupby("grupo").QT_VOTOS.sum()
cadeiras = {g: int(t // qe) for g, t in grupos.items()}

cand = v[v.nominal].sort_values("QT_VOTOS", ascending=False)
eleitos = []
for g, n in cadeiras.items():  # vagas do quociente partidário (mínimo 10% do QE)
    c = cand[(cand.grupo == g) & (cand.QT_VOTOS >= 0.10 * qe)].head(n)
    eleitos += c.index.tolist()
    cadeiras[g] = len(c)

# sobras: maiores médias, partidos com >= 80% do QE, candidatos com >= 20% do QE
while sum(cadeiras.values()) < VAGAS:
    melhor, media = None, -1
    for g, t in grupos.items():
        if t < 0.8 * qe:
            continue
        disp = cand[(cand.grupo == g) & (cand.QT_VOTOS >= 0.20 * qe) & (~cand.index.isin(eleitos))]
        if disp.empty:
            continue
        m = t / (cadeiras.get(g, 0) + 1)
        if m > media:
            melhor, media = g, m
    if melhor is None:
        break
    c = cand[(cand.grupo == melhor) & (cand.QT_VOTOS >= 0.20 * qe) & (~cand.index.isin(eleitos))].head(1)
    eleitos += c.index.tolist()
    cadeiras[melhor] = cadeiras.get(melhor, 0) + 1

el = cand.loc[eleitos].sort_values("QT_VOTOS", ascending=False)
el.to_csv("eleitos_2022_simulado.csv", index=False, encoding="utf-8")
nao = cand[~cand.index.isin(eleitos)]
res = {
    "votos_validos": validos,
    "quociente_eleitoral": qe,
    "eleitos_simulados": len(el),
    "menor_votacao_eleito": int(el.QT_VOTOS.min()),
    "mediana_eleitos": int(el.QT_VOTOS.median()),
    "maior_votacao_nao_eleito": int(nao.QT_VOTOS.max()),
    "eleitos_abaixo_de_35mil": int((el.QT_VOTOS < 35000).sum()),
    "mdb_2022_votos": int(grupos.get("15", 0)),
    "mdb_2022_cadeiras": int(cadeiras.get("15", 0)),
}
json.dump(res, open("corte_2022.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=2))
print(el[["NR_VOTAVEL", "NM_VOTAVEL", "grupo", "QT_VOTOS"]].to_string(index=False))
