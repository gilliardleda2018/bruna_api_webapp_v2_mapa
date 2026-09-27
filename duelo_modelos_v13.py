"""Modelos de ML do duelo Bruna Pessoa (estreante) × Abigail Cunha (deputada com mandato).

1. Regressão linear de incumbência: deputados entre os 42 mais votados de 2018 que voltaram em 2022.
   log(votos 2022 no município) ~ log(votos 2018 no município) + log(eleitorado)
   -> aplicada à Abigail (2022 -> 2026), com o erro do modelo (resíduos) para gerar incerteza.
   Também mede o crescimento TOTAL de quem tinha mandato (média e dispersão).
2. Classificação das seções de Barra do Corda: "Trincheira Pessoa" (Fernando 2018 > Abigail 2022)
   × "Reduto Abigail", com Regressão Logística e Random Forest (validação cruzada).
3. Monte Carlo do duelo: probabilidade de Bruna superar Abigail (total, Barra do Corda, campo neutro).

Saídas: duelo_ml_resumo.json, duelo_abigail_2026_municipios.csv, duelo_barra_secoes_classificadas.csv
"""
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEMENTE, N_SIM = 42, 20_000
rng = np.random.default_rng(SEMENTE)
TSE = Path(__file__).resolve().parent.parent / "dados_tse"
ABIGAIL = 22200


def norm(nome):
    return unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().upper().strip()


# ------------------------------------------------------------------
# 1. Regressão de incumbência
# ------------------------------------------------------------------
def votos(ano):
    v = pd.read_csv(TSE / f"votos_{ano}_municipio.csv")
    v = v[(v.DS_CARGO == "Deputado Estadual") & (v.NR_VOTAVEL >= 100)].copy()
    v["nome"] = v.NM_VOTAVEL.map(norm)
    return v


v18, v22 = votos(2018), votos(2022)
tot18 = v18.groupby("nome").QT_VOTOS.sum().sort_values(ascending=False)
tot22 = v22.groupby("nome").QT_VOTOS.sum()
incumbentes = [n for n in tot18.head(42).index if n in tot22.index]  # proxy de "eleitos em 2018"

def total_municipio(ano):
    t = pd.read_csv(TSE / f"total_votos_{ano}_municipio.csv")
    return t[t.DS_CARGO == "Deputado Estadual"].set_index("CD_MUNICIPIO").QT_VOTOS


e18, e22 = total_municipio(2018), total_municipio(2022)
pares = (v18[v18.nome.isin(incumbentes)].groupby(["nome", "CD_MUNICIPIO"]).QT_VOTOS.sum().rename("v18").to_frame()
         .join(v22[v22.nome.isin(incumbentes)].groupby(["nome", "CD_MUNICIPIO"]).QT_VOTOS.sum().rename("v22"),
               how="outer").fillna(0).reset_index())
pares["pct18"] = 100 * pares.v18 / pares.CD_MUNICIPIO.map(e18)
pares["pct22"] = 100 * pares.v22 / pares.CD_MUNICIPIO.map(e22)
pares["peso"] = pares.CD_MUNICIPIO.map(e22)
pares = pares.dropna()
# regressão linear no % do município, ponderada pelo eleitorado
X, y, w = pares[["pct18"]].values, pares.pct22.values, pares.peso.values
reg = LinearRegression()
oof = cross_val_predict(reg, X, y, cv=KFold(5, shuffle=True, random_state=SEMENTE), params={"sample_weight": w})
reg.fit(X, y, sample_weight=w)
crescimento_total = (tot22[incumbentes] / tot18[incumbentes])
redutos = pares[pares.pct18 >= 20]
retencao = redutos.pct22 / redutos.pct18
RETENCAO_CASA = (0.6, 1.0)  # premissa: cidade natal retém entre 60% e 100% do % de 2022
metricas_reg = {
    "incumbentes_analisados": len(incumbentes),
    "pares_municipio": int(len(pares)),
    "r2_validacao_cruzada": round(float(r2_score(y, oof, sample_weight=w)), 3),
    "coeficiente": round(float(reg.coef_[0]), 3),
    "intercepto": round(float(reg.intercept_), 3),
    "crescimento_total_mediano": round(float(crescimento_total.median()), 3),
    "crescimento_total_p25": round(float(crescimento_total.quantile(.25)), 3),
    "crescimento_total_p75": round(float(crescimento_total.quantile(.75)), 3),
    "pct_incumbentes_que_cresceram": round(float((crescimento_total > 1).mean()), 3),
    "redutos_analisados": int(len(redutos)),
    "retencao_reduto_mediana": round(float(retencao.median()), 3),
    "retencao_reduto_p25": round(float(retencao.quantile(.25)), 3),
    "retencao_reduto_p75": round(float(retencao.quantile(.75)), 3),
    "retencao_casa_premissa": RETENCAO_CASA,
}

base = pd.read_csv("previsao_v13_municipios.csv")
ab = base[["CD_MUNICIPIO", "municipio", "abigail_2022", "total_dep_est_2022", "votos_projetados",
           "votos_p10", "votos_p90", "dist_tuntum_km"]].copy()
ab["pct_abigail_2022"] = 100 * ab.abigail_2022 / ab.total_dep_est_2022
eleitores_26 = ab.total_dep_est_2022 * 1.03
CASA = ab.municipio == "Barra do Corda"
ab["abigail_2026"] = (reg.predict(ab[["pct_abigail_2022"]].values).clip(0) / 100 * eleitores_26)
ab.loc[CASA, "abigail_2026"] = ab.loc[CASA, "pct_abigail_2022"] * np.mean(RETENCAO_CASA) / 100 * eleitores_26[CASA]
# fora de casa, a regressão é recalibrada para o total seguir o crescimento típico de quem tem mandato
alvo_total = ab.abigail_2022.sum() * crescimento_total.median()
fora = ~CASA
ab.loc[fora, "abigail_2026"] *= (alvo_total - ab.loc[CASA, "abigail_2026"].sum()) / ab.loc[fora, "abigail_2026"].sum()
ab["abigail_2026"] = ab.abigail_2026.round()
ab.to_csv("duelo_abigail_2026_municipios.csv", index=False, encoding="utf-8")

# ------------------------------------------------------------------
# 2. Classificação das seções de Barra do Corda
# ------------------------------------------------------------------
proj = pd.read_csv("projecao_secoes_v13.csv")
cols = ["NR_TURNO", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO", "NR_VOTAVEL", "QT_VOTOS"]
cod_barra = int(base.loc[base.municipio == "Barra do Corda", "CD_MUNICIPIO"].iloc[0])
partes = []
for ch in pd.read_csv(TSE / "votacao_secao_2022_MA.csv", sep=";", encoding="latin1", usecols=cols,
                      chunksize=1_000_000):
    partes.append(ch[(ch.NR_TURNO == 1) & (ch.CD_MUNICIPIO == cod_barra) & (ch.DS_CARGO == "Deputado Estadual")])
d = pd.concat(partes)
por_secao = d.pivot_table(index=["NR_ZONA", "NR_SECAO"], columns="NR_VOTAVEL", values="QT_VOTOS",
                          aggfunc="sum", fill_value=0)
feat = pd.DataFrame({
    "abigail_2022": por_secao.get(ABIGAIL, 0),
    "brancos_nulos": por_secao.get(95, 0) + por_secao.get(96, 0),
    "total": por_secao.sum(axis=1),
}).reset_index().rename(columns={"NR_ZONA": "zona", "NR_SECAO": "secao"})
sb = proj[proj.municipio == "Barra do Corda"].merge(feat, on=["zona", "secao"], how="inner")
sb["rural"] = sb.endereco.str.contains("Povoado|Aldeia|Assentamento|Fazenda|Zona Rural|Pov",
                                       case=False, na=False).astype(int)
sb["indigena"] = sb.local_votacao.str.contains("Indigena|Indígena", case=False, na=False).astype(int)
sb["pct_eric_2022"] = 100 * sb.eric_2022 / sb.total
sb["pct_brancos_nulos"] = 100 * sb.brancos_nulos / sb.total
sb["alvo_trincheira"] = (sb.fernando_2018 > sb.abigail_2022).astype(int)
FEAT = {"total": "Tamanho da seção", "rural": "Seção rural (povoado)", "indigena": "Aldeia indígena",
        "pct_eric_2022": "% do Eric em 2022", "pct_brancos_nulos": "% brancos e nulos"}
Xc, yc = sb[list(FEAT)].values, sb.alvo_trincheira.values
cv = StratifiedKFold(5, shuffle=True, random_state=SEMENTE)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
floresta = RandomForestClassifier(n_estimators=400, min_samples_leaf=3, random_state=SEMENTE)
acc_log = cross_val_score(logit, Xc, yc, cv=cv, scoring="accuracy").mean()
acc_rf = cross_val_score(floresta, Xc, yc, cv=cv, scoring="accuracy").mean()
auc_log = cross_val_score(logit, Xc, yc, cv=cv, scoring="roc_auc").mean()
auc_rf = cross_val_score(floresta, Xc, yc, cv=cv, scoring="roc_auc").mean()
melhor_nome, melhor = (("Random Forest", floresta) if auc_rf >= auc_log else ("Regressão Logística", logit))
sb["prob_trincheira"] = cross_val_predict(melhor, Xc, yc, cv=cv, method="predict_proba")[:, 1].round(3)
melhor.fit(Xc, yc)
logit.fit(Xc, yc)
coefs = dict(zip(FEAT.values(), logit[-1].coef_[0].round(3)))
sb["classe_prevista"] = np.where(sb.prob_trincheira >= .5, "Trincheira Pessoa", "Reduto Abigail")
sb[["zona", "secao", "secao_txt", "local_votacao", "endereco", "total", "rural", "indigena", "fernando_2018",
    "abigail_2022", "eric_2022", "bruna_projetados", "alvo_trincheira", "prob_trincheira", "classe_prevista"]].to_csv(
    "duelo_barra_secoes_classificadas.csv", index=False, encoding="utf-8")
metricas_clf = {
    "secoes": int(len(sb)), "trincheiras_2018_2022": int(yc.sum()),
    "acuracia_logistica": round(float(acc_log), 3), "auc_logistica": round(float(auc_log), 3),
    "acuracia_random_forest": round(float(acc_rf), 3), "auc_random_forest": round(float(auc_rf), 3),
    "acuracia_chute_maioria": round(float(max(yc.mean(), 1 - yc.mean())), 3),
    "modelo_escolhido": melhor_nome, "coeficientes_logistica": coefs,
    "secoes_disputaveis": int(((sb.prob_trincheira >= .35) & (sb.prob_trincheira < .65)).sum()),
}

# ------------------------------------------------------------------
# 3. Monte Carlo do duelo
# ------------------------------------------------------------------
res_bruna = json.load(open("resumo_v13.json", encoding="utf-8"))["simulacao"]
# Bruna: reamostra o total da distribuição simulada (histograma do modelo principal)
bordas = np.array(res_bruna["bordas"]); pesos = np.array(res_bruna["histograma"], float)
idx = rng.choice(len(pesos), N_SIM, p=pesos / pesos.sum())
bruna_total = rng.uniform(bordas[idx], bordas[idx + 1])
# Abigail: crescimento total sorteado da distribuição real dos incumbentes + ruído
cresc = rng.choice(crescimento_total.values, N_SIM) * rng.lognormal(0, 0.05, N_SIM)
abigail_total = ab.abigail_2022.sum() * cresc
# Barra do Corda: Abigail retém entre 60% e 100% do % de 2022; Bruna segue a projeção do modelo principal
abigail_barra = (ab.loc[CASA, "pct_abigail_2022"].iloc[0] / 100 * float(eleitores_26[CASA].iloc[0])
                 * rng.uniform(*RETENCAO_CASA, N_SIM))
bruna_barra = bruna_total * float(ab.loc[CASA, "votos_projetados"].iloc[0] / ab.votos_projetados.sum())     * rng.lognormal(0, .15, N_SIM)
viz = ab[(ab.dist_tuntum_km <= 150) & ~ab.municipio.isin(["Tuntum", "Barra do Corda"])]
fr_ab = viz.abigail_2026.sum() / ab.loc[fora, "abigail_2026"].sum()
abigail_neutro = np.clip(abigail_total - abigail_barra, 0, None) * fr_ab * rng.lognormal(0, .10, N_SIM)
bruna_neutro = bruna_total * viz.votos_projetados.sum() / ab.votos_projetados.sum() * rng.lognormal(0, .15, N_SIM)
duelo = {
    "prob_bruna_supera_abigail_total": round(float((bruna_total > abigail_total).mean()), 3),
    "prob_bruna_supera_abigail_barra": round(float((bruna_barra > abigail_barra).mean()), 3),
    "prob_bruna_supera_abigail_regiao": round(float((bruna_neutro > abigail_neutro).mean()), 3),
    "abigail_2026_p10": int(np.percentile(abigail_total, 10)), "abigail_2026_p50": int(np.percentile(abigail_total, 50)),
    "abigail_2026_p90": int(np.percentile(abigail_total, 90)),
    "bruna_p50": int(np.percentile(bruna_total, 50)),
    "abigail_barra_p50": int(np.percentile(abigail_barra, 50)), "bruna_barra_p50": int(np.percentile(bruna_barra, 50)),
    "abigail_regiao_p50": int(np.percentile(abigail_neutro, 50)), "bruna_regiao_p50": int(np.percentile(bruna_neutro, 50)),
    "municipios_regiao": int(len(viz)),
}

resumo = {"regressao_incumbencia": metricas_reg, "classificacao_barra": metricas_clf, "duelo": duelo}
json.dump(resumo, open("duelo_ml_resumo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(resumo, ensure_ascii=False, indent=1))
