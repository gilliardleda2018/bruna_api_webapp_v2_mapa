"""O clássico Tuntum × Barra do Corda: Bruna Pessoa (Tuntum) × Abigail Cunha (Barra do Corda).

Saídas:
- duelo_tuntum_bairros.csv   Abigail 2022 × projeção Bruna, bairro a bairro em Tuntum
- duelo_barra_locais.csv     Abigail 2022 × Fernando 2018 × projeção Bruna, por local de votação em Barra do Corda
- duelo_campo_neutro.csv     municípios vizinhos onde as duas disputam
- duelo_resumo.json
"""
import json
from pathlib import Path

import pandas as pd

TSE = Path(__file__).resolve().parent.parent / "dados_tse"
ABIGAIL, FERNANDO = 22200, 77800

base = pd.read_csv("previsao_v13_municipios.csv")
proj = pd.read_csv("projecao_secoes_v13.csv")
tun_sec = pd.read_csv("tuntum_secoes_v13.csv")
cod = base.set_index("cidade_norm").CD_MUNICIPIO
COD_TUNTUM, COD_BARRA = int(cod["tuntum"]), int(cod["barra do corda"])


def abigail_por_secao(cd_municipio):
    cols = ["NR_TURNO", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO", "NR_VOTAVEL", "QT_VOTOS"]
    partes = []
    for ch in pd.read_csv(TSE / "votacao_secao_2022_MA.csv", sep=";", encoding="latin1", usecols=cols,
                          chunksize=1_000_000):
        partes.append(ch[(ch.NR_TURNO == 1) & (ch.CD_MUNICIPIO == cd_municipio)
                         & (ch.DS_CARGO == "Deputado Estadual") & (ch.NR_VOTAVEL == ABIGAIL)])
    d = pd.concat(partes)
    return d.groupby(["NR_ZONA", "NR_SECAO"]).QT_VOTOS.sum().rename("abigail_2022").reset_index()


# ---------- Tuntum, bairro a bairro ----------
ab_t = abigail_por_secao(COD_TUNTUM)
tun_sec["abigail_2022"] = tun_sec.secao.map(ab_t.set_index("NR_SECAO").abigail_2022).fillna(0).astype(int)
tun_sec["bairro"] = tun_sec.bairro.str.title()
duelo_t = (tun_sec.groupby("bairro")
           .agg(bruna_projecao=("bruna_realista", "sum"), abigail_2022=("abigail_2022", "sum"),
                fernando_prefeito_2024=("fernando_2024", "sum"))
           .reset_index().sort_values("bruna_projecao", ascending=False))
duelo_t.to_csv("duelo_tuntum_bairros.csv", index=False, encoding="utf-8")

# ---------- Barra do Corda, local a local ----------
ab_b = abigail_por_secao(COD_BARRA).rename(columns={"NR_ZONA": "zona", "NR_SECAO": "secao"})
pb = proj[proj.municipio == "Barra do Corda"].merge(ab_b, on=["zona", "secao"], how="left")
pb["abigail_2022"] = pb.abigail_2022.fillna(0)
duelo_b = (pb.groupby("local_votacao")
           .agg(secoes=("secao", "count"), votantes=("votos_dep_est_2022", "sum"),
                bruna_projecao=("bruna_projetados", "sum"), fernando_2018=("fernando_2018", "sum"),
                abigail_2022=("abigail_2022", "sum"), endereco=("endereco", "first"))
           .reset_index())
duelo_b["resultado_2018_2022"] = (duelo_b.fernando_2018 > duelo_b.abigail_2022).map(
    {True: "Trincheira Pessoa", False: "Reduto Abigail"})
duelo_b = duelo_b.sort_values("fernando_2018", ascending=False)
duelo_b.to_csv("duelo_barra_locais.csv", index=False, encoding="utf-8")

# ---------- campo neutro: vizinhos onde as duas têm voto ----------
viz = base[(base.cidade_norm.isin(["tuntum", "barra do corda"]) == False)
           & ((base.abigail_2022 >= 300) | (base.votos_projetados >= 300))
           & (base.dist_tuntum_km <= 250)]
neutro = viz[["municipio", "dist_tuntum_km", "votos_projetados", "abigail_2022", "fernando_pessoa_2018",
              "total_dep_est_2022"]].copy()
neutro["abigail_2026_est"] = (neutro.abigail_2022 * 1.03).round()
neutro["vantagem_bruna"] = neutro.votos_projetados - neutro.abigail_2026_est
neutro = neutro.sort_values("abigail_2022", ascending=False)
neutro.to_csv("duelo_campo_neutro.csv", index=False, encoding="utf-8")

bt = base.set_index("cidade_norm")
resumo = {
    "tuntum": {"bruna": int(duelo_t.bruna_projecao.sum()), "abigail_2022": int(duelo_t.abigail_2022.sum()),
               "votantes": int(tun_sec.comparecimento_2024.sum())},
    "barra": {"bruna": int(duelo_b.bruna_projecao.sum()), "abigail_2022": int(duelo_b.abigail_2022.sum()),
              "fernando_2018": int(duelo_b.fernando_2018.sum()),
              "votantes": int(bt.loc["barra do corda", "total_dep_est_2022"]),
              "locais": int(len(duelo_b)),
              "trincheiras": int((duelo_b.resultado_2018_2022 == "Trincheira Pessoa").sum())},
    "estado": {"bruna": int(base.votos_projetados.sum()), "abigail_2022": int(base.abigail_2022.sum())},
    "campo_neutro": {"municipios": int(len(neutro)), "bruna_na_frente": int((neutro.vantagem_bruna > 0).sum())},
}
json.dump(resumo, open("duelo_resumo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(resumo, ensure_ascii=False, indent=1))
print(duelo_t.head(8).to_string(index=False))
print(duelo_b.head(8)[["local_votacao", "fernando_2018", "abigail_2022", "bruna_projecao", "resultado_2018_2022"]].to_string(index=False))
print(neutro.to_string(index=False))
