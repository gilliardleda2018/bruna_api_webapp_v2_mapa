"""Projeção da Bruna por seção eleitoral (e por bairro / local de votação).

- Tuntum: calibração própria (voto do prefeito Fernando 2024 por seção × conversão observada).
- Demais municípios: a projeção municipal (modelos_v13.py) é distribuída entre as seções
  de 2022 conforme o histórico do grupo na seção:
    peso = 0,6 × participação do Fernando 2018 + 0,2 × participação do Eric 2022 + 0,2 × tamanho da seção
  (componente sem voto no município é substituído pelo tamanho da seção).

Saída: projecao_secoes_v13.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

TSE = Path(__file__).resolve().parent.parent / "dados_tse"
MIN_VOTOS_MUNICIPIO = 100  # só municípios com projeção relevante

base = pd.read_csv("previsao_v13_municipios.csv")
alvo = base[base.votos_projetados >= MIN_VOTOS_MUNICIPIO]
codigos = set(alvo.CD_MUNICIPIO)
tun = json.load(open("tuntum_resumo_v13.json", encoding="utf-8"))


def ler_secoes(ano, numero):
    cols = ["NR_TURNO", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO", "NR_VOTAVEL", "QT_VOTOS",
            "NM_LOCAL_VOTACAO", "DS_LOCAL_VOTACAO_ENDERECO"]
    partes = []
    for ch in pd.read_csv(TSE / f"votacao_secao_{ano}_MA.csv", sep=";", encoding="latin1",
                          usecols=cols, chunksize=1_000_000):
        ch = ch[(ch.NR_TURNO == 1) & (ch.DS_CARGO == "Deputado Estadual") & ch.CD_MUNICIPIO.isin(codigos)]
        partes.append(ch)
    d = pd.concat(partes)
    chave = ["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
    tot = d.groupby(chave).QT_VOTOS.sum().rename(f"votos_dep_est_{ano}")
    cand = d[d.NR_VOTAVEL == numero].groupby(chave).QT_VOTOS.sum().rename(f"cand_{ano}")
    local = d.groupby(chave)[["NM_LOCAL_VOTACAO", "DS_LOCAL_VOTACAO_ENDERECO"]].first()
    return pd.concat([tot, cand, local], axis=1).reset_index()


s22 = ler_secoes(2022, 55800).rename(columns={"cand_2022": "eric_2022"})
s18 = ler_secoes(2018, 77800).rename(columns={"cand_2018": "fernando_2018"})
sec = s22.merge(s18[["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "fernando_2018"]],
                on=["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"], how="left")
sec[["eric_2022", "fernando_2018"]] = sec[["eric_2022", "fernando_2018"]].fillna(0)
sec = sec.merge(alvo[["CD_MUNICIPIO", "municipio", "votos_projetados", "votos_p10", "votos_p90"]],
                on="CD_MUNICIPIO")


def participacao(col, grupo):
    soma = grupo[col].sum()
    return grupo[col] / soma if soma > 0 else grupo["votos_dep_est_2022"] / grupo["votos_dep_est_2022"].sum()


pesos = []
for _, g in sec.groupby("CD_MUNICIPIO"):
    w = (0.6 * participacao("fernando_2018", g) + 0.2 * participacao("eric_2022", g)
         + 0.2 * participacao("votos_dep_est_2022", g))
    pesos.append(w)
sec["peso"] = pd.concat(pesos)
for c in ["votos_projetados", "votos_p10", "votos_p90"]:
    sec[c.replace("votos_", "bruna_")] = (sec[c] * sec.peso).round(1)
sec["bairro"] = ""
sec["fonte_projecao"] = "histórico do grupo na seção"

# ---------- Tuntum: substitui pela calibração com o voto do prefeito 2024 ----------
ts = pd.read_csv("tuntum_secoes_v13.csv")
mt = base.loc[base.cidade_norm == "tuntum"].iloc[0]
fator_p10, fator_p90 = mt.votos_p10 / mt.votos_projetados, mt.votos_p90 / mt.votos_projetados
tt = pd.DataFrame({
    "CD_MUNICIPIO": mt.CD_MUNICIPIO, "municipio": "Tuntum", "NR_ZONA": 79, "NR_SECAO": ts.secao,
    "secao_txt": ts.secao_txt, "NM_LOCAL_VOTACAO": ts.local, "bairro": ts.bairro.str.title(),
    "votos_dep_est_2022": ts.comparecimento_2024, "eric_2022": ts.eric, "fernando_2018": np.nan,
    "fernando_prefeito_2024": ts.fernando_2024, "tema_prefeito_2024": ts.tema_2024,
    "bruna_projetados": ts.bruna_realista, "bruna_p10": (ts.bruna_realista * fator_p10).round(1),
    "bruna_p90": (ts.bruna_realista * fator_p90).round(1),
    "fonte_projecao": "voto do prefeito 2024 × conversão observada",
})
sec = pd.concat([sec[sec.municipio != "Tuntum"], tt], ignore_index=True)
sec["secao_txt"] = sec["secao_txt"].fillna("Seção " + sec.NR_SECAO.astype(int).astype(str).str.zfill(3))
sec["local_votacao"] = sec.NM_LOCAL_VOTACAO.str.title()
sec["endereco"] = sec.DS_LOCAL_VOTACAO_ENDERECO.fillna("").str.title()
sec["pct_bruna_estimado"] = (100 * sec.bruna_projetados / sec.votos_dep_est_2022).round(1)

saida = sec[["municipio", "NR_ZONA", "NR_SECAO", "secao_txt", "bairro", "local_votacao", "endereco",
             "votos_dep_est_2022", "fernando_2018", "eric_2022", "fernando_prefeito_2024", "tema_prefeito_2024",
             "bruna_p10", "bruna_projetados", "bruna_p90", "pct_bruna_estimado", "fonte_projecao"]]
saida = saida.rename(columns={"NR_ZONA": "zona", "NR_SECAO": "secao"}).sort_values(
    ["municipio", "zona", "secao"])
saida.to_csv("projecao_secoes_v13.csv", index=False, encoding="utf-8")

conf = saida.groupby("municipio").bruna_projetados.sum().round()
ref = alvo.set_index("municipio").votos_projetados
print(f"{len(saida)} seções em {saida.municipio.nunique()} municípios")
print("diferença máx. soma-seções × projeção municipal:", float((conf - ref.reindex(conf.index)).abs().max()))
print(saida[saida.municipio == "Barra do Corda"].nlargest(5, "bruna_projetados").to_string(index=False))
