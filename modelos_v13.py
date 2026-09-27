"""Modelos V13 — estratégia da reta final (Bruna Pessoa, dep. estadual MA/MDB).

1. Potencial do grupo (Gradient Boosting): aprende onde o grupo Pessoa tem voto
   (alvo: % do Fernando Pessoa em 2018) a partir de geografia, porte e do mapa
   de 2022. Predições fora da amostra (validação cruzada) viram "potencial".
2. Projeção 2026 por município: voto herdado do grupo + voto histórico
   recuperável + rede de lideranças de campo.
3. Simulação Monte Carlo (20 mil cenários) com incerteza em cada taxa.
4. Segmentação (K-Means) em perfis estratégicos.
5. Agenda da reta final: onde uma visita move mais votos, com rota por dia.

Saídas: previsao_v13_municipios.csv, agenda_v13.csv, resumo_v13.json
"""
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import StandardScaler

SEMENTE = 42
N_SIM = 20_000
rng = np.random.default_rng(SEMENTE)

base = pd.read_csv("base_v13_municipios.csv")
corte = json.load(open("corte_2022.json", encoding="utf-8"))
tuntum_sec = json.load(open("tuntum_resumo_v13.json", encoding="utf-8"))
IDX_TUNTUM = int(np.flatnonzero(base.cidade_norm == "tuntum")[0])

# Premissas centrais (o painel permite mexer nelas)
PREMISSAS = {
    "taxa_transferencia": 0.78,  # quanto do voto que seguiu o grupo em 2018/2022 vem para Bruna
    "taxa_recuperacao_2018": 0.35,  # eleitor do Fernando 2018 que não foi de Eric em 2022
    "taxa_realizacao_campo": 0.50,  # quanto da expectativa das lideranças vira voto
    "crescimento_eleitorado": 0.03,
    # Tuntum: conversão do voto do prefeito Fernando (2024) em voto de deputado, medida seção a seção
    "conversao_tuntum": tuntum_sec["conversao"]["realista"],
}
REFERENCIAS = {
    "menor_eleito_2022": corte["menor_votacao_eleito"],
    "ultimo_eleito_chapa_governo_2022": 38329,  # PSB 2022, 12º eleito da chapa
    "mediana_eleitos_2022": corte["mediana_eleitos"],
}

# ------------------------------------------------------------------
# 1. Modelo de potencial do grupo
# ------------------------------------------------------------------
base["log_eleitores"] = np.log1p(base["total_dep_est_2022"])
FEATURES = {
    "dist_tuntum_km": "Distância de Tuntum",
    "log_eleitores": "Tamanho do eleitorado",
    "lat": "Latitude",
    "lon": "Longitude",
    "pct_eric_costa_2022": "Voto do Eric em 2022",
    "pct_abigail_2022": "Voto da Abigail em 2022",
    "pct_daniella_2022": "Voto da Daniella em 2022",
    "pct_daniella_2018": "Voto da Daniella em 2018",
}
X = base[list(FEATURES)].values
y = np.log1p(base["pct_fernando_pessoa_2018"].values)
modelo = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05,
                                   subsample=0.8, random_state=SEMENTE)
kf = KFold(n_splits=5, shuffle=True, random_state=SEMENTE)
oof = cross_val_predict(modelo, X, y, cv=kf)
base["pct_potencial_ml"] = np.expm1(oof).clip(0).round(2)
metricas_ml = {
    "r2_validacao_cruzada": round(r2_score(y, oof), 3),
    "erro_medio_pontos_pct": round(mean_absolute_error(np.expm1(y), np.expm1(oof)), 2),
    "municipios_treino": int(len(base)),
}
modelo.fit(X, y)
imp = permutation_importance(modelo, X, y, n_repeats=20, random_state=SEMENTE)
importancias = sorted(({"variavel": FEATURES[f], "importancia": round(float(v), 4)}
                       for f, v in zip(FEATURES, imp.importances_mean)),
                      key=lambda d: -d["importancia"])

# ------------------------------------------------------------------
# 2. Projeção determinística por município
# ------------------------------------------------------------------
def projetar(df, taxa_transf, taxa_rec, taxa_campo, cresc, choque=1.0, conv_tuntum=None, choque_tuntum=1.0):
    eleitores = df["total_dep_est_2022"].values * (1 + cresc)
    sobrep = df["pct_sobreposicao"].values / 100
    extra_2018 = np.clip(df["pct_fernando_pessoa_2018"].values / 100 - sobrep, 0, None)
    hist = eleitores * (taxa_transf * sobrep + taxa_rec * extra_2018)
    campo = df["expectativa_total"].values * taxa_campo
    # rede de campo e histórico se sobrepõem: vale o maior + 20% do menor
    total = (np.maximum(hist, campo) + 0.2 * np.minimum(hist, campo)) * choque
    if conv_tuntum is not None:  # Tuntum usa a calibração por seção
        total[IDX_TUNTUM] = tuntum_sec["fernando_2024"] * conv_tuntum * choque_tuntum
    return total, hist, campo


p = PREMISSAS
proj, hist, campo = projetar(base, p["taxa_transferencia"], p["taxa_recuperacao_2018"],
                             p["taxa_realizacao_campo"], p["crescimento_eleitorado"],
                             conv_tuntum=p["conversao_tuntum"])
base["votos_historico"] = hist.round()
base["votos_rede_campo"] = campo.round()
base["votos_projetados"] = proj.round()

# ------------------------------------------------------------------
# 3. Monte Carlo
# ------------------------------------------------------------------
def beta(media, dp, n):
    k = media * (1 - media) / dp ** 2 - 1
    return rng.beta(media * k, (1 - media) * k, n)


t_transf = beta(p["taxa_transferencia"], 0.08, N_SIM)
t_rec = beta(p["taxa_recuperacao_2018"], 0.10, N_SIM)
t_campo = beta(p["taxa_realizacao_campo"], 0.15, N_SIM)
cresc = rng.normal(p["crescimento_eleitorado"], 0.02, N_SIM)
conv_t = rng.uniform(tuntum_sec["conversao"]["conservador"], tuntum_sec["conversao"]["forte"], N_SIM)
regioes = base["regiao_intermediaria"].astype("category").cat.codes.values
choque_reg = rng.lognormal(0, 0.12, (N_SIM, regioes.max() + 1))[:, regioes]
choque_mun = rng.lognormal(0, 0.25, (N_SIM, len(base)))
choque_geral = rng.lognormal(-0.02, 0.12, N_SIM)  # clima da campanha como um todo

sims = np.empty((N_SIM, len(base)))
for i in range(N_SIM):
    sims[i], _, _ = projetar(base, t_transf[i], t_rec[i], t_campo[i], cresc[i],
                             choque_geral[i] * choque_reg[i] * choque_mun[i], conv_tuntum=conv_t[i],
                             choque_tuntum=choque_geral[i])
totais = sims.sum(axis=1)
base["votos_p10"] = np.percentile(sims, 10, axis=0).round()
base["votos_p90"] = np.percentile(sims, 90, axis=0).round()
base["votos_em_jogo"] = (base["votos_p90"] - base["votos_p10"]).round()

simulacao = {
    "media": int(totais.mean()),
    "p10": int(np.percentile(totais, 10)),
    "p50": int(np.percentile(totais, 50)),
    "p90": int(np.percentile(totais, 90)),
    "prob_acima": {k: round(float((totais >= v).mean()), 3) for k, v in REFERENCIAS.items()},
    "histograma": np.histogram(totais, bins=40)[0].tolist(),
    "bordas": np.histogram(totais, bins=40)[1].round().tolist(),
}
# sensibilidade: quanto cada premissa move o total (correlação com o resultado)
sensibilidade = {
    "Transferência do grupo (eleitor do Eric em 2022)": round(float(np.corrcoef(t_transf, totais)[0, 1]), 2),
    "Recuperação do eleitor do Fernando 2018": round(float(np.corrcoef(t_rec, totais)[0, 1]), 2),
    "Entrega das lideranças de campo": round(float(np.corrcoef(t_campo, totais)[0, 1]), 2),
    "Conversão do voto do prefeito em Tuntum": round(float(np.corrcoef(conv_t, totais)[0, 1]), 2),
}

# ------------------------------------------------------------------
# 4. Adversários: impacto estimado da mudança de apoio
# ------------------------------------------------------------------
perda_eric = int((base["votos_fieis_grupo"] * p["taxa_transferencia"]).sum())
adversarios = {
    "Abigail Cunha": {"votos_2022": int(base.abigail_2022.sum()), "estimativa_2026": int(base.abigail_2022.sum() * 1.03),
                       "nota": "Base preservada; disputa direta com Bruna em Barra do Corda e Fernando Falcão."},
    "Daniella": {"votos_2022": int(base.daniella_2022.sum()), "estimativa_2026": int(base.daniella_2022.sum() * 1.03),
                 "nota": "Base em Caxias e Presidente Dutra; pouca sobreposição com Bruna."},
    "Eric Costa": {"votos_2022": int(base.eric_costa_2022.sum()),
                   "estimativa_2026": int(base.eric_costa_2022.sum() * 1.03 - perda_eric),
                   "nota": f"Perde o apoio do grupo Pessoa: cerca de {perda_eric:,} votos em jogo, sobretudo Tuntum e Itaipava.".replace(",", ".")},
    "César Ferro": {"votos_2022": 0, "estimativa_2026": None,
                    "nota": "Estreante para deputado estadual; sem histórico no TSE."},
}

# ------------------------------------------------------------------
# 5. Segmentação estratégica (K-Means)
# ------------------------------------------------------------------
SEG_COLS = ["pct_sobreposicao", "pct_fernando_pessoa_2018", "pct_abigail_2022",
            "pct_eric_costa_2022", "pct_daniella_2022", "log_eleitores", "dist_tuntum_km"]
base["campo_por_mil_eleitores"] = 1000 * base.expectativa_total / base.total_dep_est_2022
SEG_COLS.append("campo_por_mil_eleitores")
Z = StandardScaler().fit_transform(base[SEG_COLS])
km = KMeans(n_clusters=6, n_init=20, random_state=SEMENTE).fit(Z)
base["segmento_id"] = km.labels_
perfil = base.groupby("segmento_id")[SEG_COLS + ["votos_projetados"]].mean()

NOMES = [  # (nome, métrica que define, ação)
    ("Fortaleza Pessoa", "pct_sobreposicao", "Blindar: garantir que todo eleitor saiba que agora o voto é Bruna."),
    ("Território Abigail", "pct_abigail_2022", "Disputa direta: presença pessoal e lideranças fortes."),
    ("Área Daniella", "pct_daniella_2022", "Baixa sobreposição: só entrar com liderança já comprometida."),
    ("Rede nova de campo", "campo_por_mil_eleitores", "Converter a rede de lideranças em voto: logística e material."),
    ("Grandes centros", "log_eleitores", "Voto de opinião: redes sociais e mídia, não agenda presencial."),
]
nome_seg, acao_seg, usados = {}, {}, set()
for nome, metrica, acao in NOMES:
    livre = perfil.drop(index=list(usados))
    if livre.empty:
        break
    sid = livre[metrica].idxmax()
    nome_seg[sid], acao_seg[sid] = nome, acao
    usados.add(sid)
for sid in perfil.index:
    if sid not in nome_seg:
        nome_seg[sid] = "Fora do radar"
        acao_seg[sid] = "Não investir agenda nesta reta final."
base["segmento"] = base.segmento_id.map(nome_seg)
base["acao_segmento"] = base.segmento_id.map(acao_seg)
segmentos = (base.groupby("segmento")
             .agg(municipios=("municipio", "count"), votos_projetados=("votos_projetados", "sum"),
                  eleitores=("total_dep_est_2022", "sum"), acao=("acao_segmento", "first"))
             .reset_index().sort_values("votos_projetados", ascending=False))

# ------------------------------------------------------------------
# 6. Agenda da reta final
# ------------------------------------------------------------------
# ganho de uma visita: parte dos votos em jogo + conversão do eleitor do Eric 2022
base["eleitor_eric_a_converter"] = (base.votos_fieis_grupo * (1 - p["taxa_transferencia"])).round()
base["ganho_visita"] = (0.20 * base.votos_em_jogo + 0.30 * base.eleitor_eric_a_converter
                        + 0.05 * base.votos_rede_campo * (1 + base.prefeito_apoia)).round()

DIAS = [("Seg 28/09", "comício"), ("Ter 29/09", "comício"), ("Qua 30/09", "comício"),
        ("Qui 01/10", "comício (último dia)"), ("Sex 02/10", "caminhada/carreata"),
        ("Sáb 03/10", "caminhada/carreata até 22h")]
HORAS_DIA, HORAS_EVENTO, KM_H, FATOR_ESTRADA = 13.0, 2.5, 60.0, 1.35


def horas_viagem(a, b):
    from math import asin, cos, radians, sin, sqrt
    dlat, dlon = radians(b.lat - a.lat), radians(b.lon - a.lon)
    h = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(h)) * FATOR_ESTRADA / KM_H


GANHO_MINIMO = 100  # abaixo disso a visita não compensa o deslocamento
idx = base.set_index("municipio")
tuntum = idx.loc["Tuntum"]
candidatas = idx[(idx.ganho_visita >= GANHO_MINIMO) & (idx.index != "Tuntum")]
atual = tuntum
agenda, visitados = [], set()
for n_dia, (dia, tipo) in enumerate(DIAS):
    ultimo_dia = n_dia == len(DIAS) - 1
    horas = HORAS_DIA - (HORAS_EVENTO if ultimo_dia else 0)  # reserva o encerramento
    ordem = 1
    while True:
        melhor, melhor_score, melhor_h = None, 0, 0
        for nome, c in candidatas.iterrows():
            if nome in visitados:
                continue
            h = horas_viagem(atual, c) + HORAS_EVENTO
            volta = horas_viagem(c, tuntum) if ultimo_dia else 0
            if h + volta > horas:
                continue
            score = c.ganho_visita / (h + volta)
            if score > melhor_score:
                melhor, melhor_score, melhor_h = nome, score, h
        if melhor is None:
            break
        c = candidatas.loc[melhor]
        agenda.append({"dia": dia, "tipo_ato": tipo, "ordem": ordem, "municipio": melhor,
                       "horas_deslocamento": round(melhor_h - HORAS_EVENTO, 1),
                       "ganho_estimado_votos": int(c.ganho_visita), "segmento": c.segmento})
        visitados.add(melhor)
        horas -= melhor_h
        atual = c
        ordem += 1
    if ultimo_dia:
        agenda.append({"dia": dia, "tipo_ato": "encerramento", "ordem": ordem, "municipio": "Tuntum",
                       "horas_deslocamento": round(horas_viagem(atual, tuntum), 1),
                       "ganho_estimado_votos": int(tuntum.ganho_visita), "segmento": tuntum.segmento})
agenda = pd.DataFrame(agenda)
agenda.to_csv("agenda_v13.csv", index=False, encoding="utf-8")

# ------------------------------------------------------------------
# 7. Lideranças: quem confirmar, quem cobrar, onde falta alguém
# ------------------------------------------------------------------
def situacao_campo(r):
    if r.tem_campo and r.expectativa_total >= 500 and r.votos_historico < 0.3 * r.expectativa_total:
        return "Cobrar e confirmar"  # promessa muito acima do que a história sustenta
    if r.tem_campo and r.votos_historico >= 0.5 * r.expectativa_total:
        return "Base confirmada pela história"
    if not r.tem_campo and r.votos_historico >= 200:
        return "Voto sem liderança: nomear responsável"
    if r.tem_campo:
        return "Acompanhar"
    return ""


base["situacao_campo"] = base.apply(situacao_campo, axis=1).replace("", "Sem campo e sem histórico")

# ------------------------------------------------------------------
# 8. Dia da eleição: fiscais e mobilização
# ------------------------------------------------------------------
secoes = pd.read_csv("../dados_tse/secoes_2022_municipio.csv")
base = base.merge(secoes, on="CD_MUNICIPIO", how="left")
base["prioridade_dia_d"] = (base.votos_projetados + 0.5 * base.votos_em_jogo).round()
base["votos_por_secao"] = (base.votos_projetados / base.secoes).round(1)

# ------------------------------------------------------------------
# Saídas
# ------------------------------------------------------------------
base.to_csv("previsao_v13_municipios.csv", index=False, encoding="utf-8")
resumo = {
    "premissas": PREMISSAS, "referencias": REFERENCIAS, "corte_2022": corte,
    "simulacao": simulacao, "sensibilidade": sensibilidade,
    "modelo_potencial": {**metricas_ml, "importancias": importancias},
    "adversarios": adversarios,
    "tuntum": tuntum_sec,
    "segmentos": segmentos.to_dict(orient="records"),
    "votos_fieis_grupo_total": int(base.votos_fieis_grupo.sum()),
    "ganho_agenda_total": int(agenda.ganho_estimado_votos.sum()) if len(agenda) else 0,
    "situacao_campo": base.situacao_campo.value_counts().to_dict(),
    "eleitor_eric_a_converter_total": int(base.eleitor_eric_a_converter.sum()),
    "votos_campo_sem_historico": int(base.loc[base.situacao_campo == "Cobrar e confirmar", "votos_projetados"].sum()),
}
json.dump(resumo, open("resumo_v13.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(json.dumps({k: resumo[k] for k in ["simulacao", "sensibilidade", "modelo_potencial"]},
                 ensure_ascii=False, indent=1)[:3000])
print(segmentos.to_string(index=False))
print(agenda.to_string(index=False))
print(base.nlargest(15, "votos_projetados")[["municipio", "segmento", "votos_historico", "votos_rede_campo",
                                            "votos_projetados", "votos_p10", "votos_p90", "expectativa_total"]].to_string(index=False))
print({k: v["estimativa_2026"] for k, v in adversarios.items()})
print(base.situacao_campo.value_counts())
print(base.nlargest(10, "prioridade_dia_d")[["municipio", "votos_projetados", "secoes", "locais_votacao", "votos_por_secao"]].to_string(index=False))
