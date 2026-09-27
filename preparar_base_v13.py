"""Base unificada V13: TSE (2018/2022) + dados de campo + geografia (IBGE).

Saídas:
- base_v13_municipios.csv  (217 municípios do MA)
- liderancas_v13.csv       (lideranças da planilha de campo, por município)
"""
import json
import math
import unicodedata
from pathlib import Path

import pandas as pd
from shapely.geometry import shape

RAIZ = Path(__file__).resolve().parent.parent
TSE = RAIZ / "dados_tse" / "base_tse_rivais_municipio.csv"
CAMPO = RAIZ / "municipios_consolidados_v9_cluster.csv"
PLANILHA = RAIZ / "CIDADES ATUALIZADO.xlsx"
GEOJSON = RAIZ / "ma_municipios.geojson"

ALIASES = {  # grafias da planilha de campo -> nome oficial normalizado
    "capinzal": "capinzal do norte",
    "sao benedito": "sao benedito do rio preto",
    "ribeiraozinho/ edison lobao": "governador edison lobao",
}
ABREVIACOES = [("gov. ", "governador "), ("pres. ", "presidente "), ("s. ", "sao ")]


def normalizar(nome):
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    s = " ".join(s.replace("-", " ").replace("'", " ").lower().split())
    for curta, longa in ABREVIACOES:
        if s.startswith(curta):
            s = longa + s[len(curta):]
    if s.endswith(" do ma"):
        s += "ranhao"
    return ALIASES.get(s, s)


def distancia_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------- geografia ----------
geo = json.load(open(GEOJSON, encoding="utf-8"))
linhas = []
for f in geo["features"]:
    p = f["properties"]
    c = shape(f["geometry"]).representative_point()
    linhas.append({
        "cd_ibge": p["CD_MUN"], "municipio": p["NM_MUN"], "cidade_norm": normalizar(p["NM_MUN"]),
        "regiao_imediata": p["NM_RGI"], "regiao_intermediaria": p["NM_RGINT"],
        "area_km2": p["AREA_KM2"], "lat": c.y, "lon": c.x,
    })
base = pd.DataFrame(linhas)
tuntum = base[base.cidade_norm == "tuntum"].iloc[0]
base["dist_tuntum_km"] = base.apply(
    lambda r: round(distancia_km(r.lat, r.lon, tuntum.lat, tuntum.lon), 1), axis=1)

# ---------- TSE ----------
tse = pd.read_csv(TSE).drop(columns=["NM_MUNICIPIO"])
tse["cidade_norm"] = tse["cidade_norm"].map(normalizar)
base = base.merge(tse, on="cidade_norm", how="left", indicator=True)
sem_tse = base[base["_merge"] == "left_only"].municipio.tolist()
base = base.drop(columns="_merge")

# ---------- campo (planilha consolidada v9) ----------
campo = pd.read_csv(CAMPO)
campo["cidade_norm"] = campo["CIDADE"].map(normalizar)
campo = campo[["cidade_norm", "expectativa_total", "total_liderancas", "peso_medio_liderancas",
               "forca_media_local", "prefeito_apoia", "sentimento_local_txt", "cluster_v9"]]
sem_geo = sorted(set(campo.cidade_norm) - set(base.cidade_norm))
base = base.merge(campo, on="cidade_norm", how="left")
base["tem_campo"] = base["expectativa_total"].notna().astype(int)
for c in ["expectativa_total", "total_liderancas", "peso_medio_liderancas",
          "forca_media_local", "prefeito_apoia"]:
    base[c] = base[c].fillna(0)
base["sentimento_local_txt"] = base["sentimento_local_txt"].fillna("sem leitura")

# ---------- lideranças (nomes, para as fichas em linguagem natural) ----------
pl = pd.read_excel(PLANILHA)
pl["CIDADE"] = pl["CIDADE"].ffill()
pl["regiao_campo"] = pl["Região - Mapa Politico "].ffill()
pl = pl[pl["CIDADE"].astype(str).str.upper() != "TOTAL"]
lid = pd.DataFrame({
    "cidade_norm": pl["CIDADE"].map(normalizar),
    "regiao_campo": pl["regiao_campo"],
    "lideranca": pl["Liderança/Grupo Politico "].astype(str).str.strip(),
    "status": pl["Foi candidato?"].fillna(""),
    "votos_que_tirou": pd.to_numeric(pl["QUANT. VOTOS TIROU"], errors="coerce"),
    "prefeito_2024": pl["CANDIDATO 2024 (PREF)"].fillna(""),
    "dep_federal_2026": pl["DEP. FEDERAL 2026"].fillna(""),
})
lid = lid[~lid.lideranca.isin(["nan", ""])]
lid.to_csv("liderancas_v13.csv", index=False, encoding="utf-8")
reg = lid.groupby("cidade_norm").regiao_campo.first()
base["regiao_campo"] = base.cidade_norm.map(reg).fillna("")

# ---------- variáveis derivadas ----------
base["eleitores_2026_est"] = (base["total_dep_est_2022"] * 1.03).round()  # crescimento ~3%
base["pct_sobreposicao"] = base[["pct_fernando_pessoa_2018", "pct_eric_costa_2022"]].min(axis=1)
# Barra do Corda: Eric é da cidade; só metade da sobreposição conta como voto do grupo
base.loc[base.cidade_norm == "barra do corda", "pct_sobreposicao"] *= 0.5
base["votos_fieis_grupo"] = (base.pct_sobreposicao / 100 * base.eleitores_2026_est).round()

base.to_csv("base_v13_municipios.csv", index=False, encoding="utf-8")
print(f"{len(base)} municípios | com campo: {base.tem_campo.sum()} | lideranças: {len(lid)}")
print("sem TSE:", sem_tse)
print("campo sem correspondência no mapa:", sem_geo)
