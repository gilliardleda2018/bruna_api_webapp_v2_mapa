"""Painel Estratégico V13 — Bruna Pessoa (Dep. Estadual MA / MDB) — reta final.

Rodar:  streamlit run dashboard_bruna_v13_estrategico.py
Dados:  gerados por preparar_base_v13.py e modelos_v13.py (mesma pasta).
"""
import base64
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PASTA = Path(__file__).resolve().parent
px.defaults.template = "plotly_white"  # gráficos em fundo branco dentro dos cartões
ELEICAO = pd.Timestamp("2026-10-04")
# Identidade visual da campanha (site oficial bruna-pessoa-15800): marinho + magenta
ROSA, MARINHO, AMARELO, CINZA, VERMELHO = "#E02597", "#122545", "#F2A900", "#8A8F98", "#E8702A"
ESCALA_ROSA = [[0, "#FDF1F8"], [0.5, "#F07BBE"], [1, "#B0126F"]]
CORES_SEGMENTO = {
    "Fortaleza Pessoa": MARINHO, "Território Abigail": VERMELHO, "Rede nova de campo": ROSA,
    "Grandes centros": "#3B6FB6", "Área Daniella": "#1A9C9C", "Fora do radar": "#E3E1E6",
}
FOTO = PASTA / "assets" / "bruna_foto_oficial.png"

st.set_page_config(page_title="Bruna Pessoa 15800 · Estratégia da Reta Final", page_icon="💗", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@700;900&family=Manrope:wght@400;600;800&display=swap');
html, body, [class*="st-"], .stMarkdown, .stMetric {font-family: 'Manrope', Arial, sans-serif;}
h1, h2, h3, h4 {font-family: 'Archivo', Arial, sans-serif !important; color: #122545;}
.block-container {padding-top: 3.6rem; max-width: 1400px;}
[data-testid="stMetricValue"] {color: #122545; font-family: 'Archivo', Arial, sans-serif; font-weight: 900;}
.stTabs [aria-selected="true"] {color: #E02597 !important;}
.cartao {border-radius: 14px; padding: 14px 18px; background: #FBEFF6; border-left: 6px solid #E02597;
         margin-bottom: 10px; color: #122545;}
.cartao.alerta {background: #FFF6E0; border-left-color: #F2A900;}
.cartao.risco {background: #EEF1F7; border-left-color: #122545;}
.cartao h4 {margin: 0 0 4px 0;}
.pequeno {font-size: .85rem; opacity: .75;}
.banner {position: relative; overflow: hidden; border-radius: 22px; min-height: 250px; margin-bottom: 14px;
         background: radial-gradient(circle at 80% 30%, rgba(224,37,151,.75), transparent 55%),
                     linear-gradient(160deg, #122545 20%, #5a2a6e);}
.banner .texto {position: relative; z-index: 2; padding: 22px 28px; max-width: 64%;}
.banner .selo {display: inline-block; border: 1px solid rgba(255,255,255,.45); color: #fff; border-radius: 999px;
               padding: 4px 12px; font: 800 .72rem 'Manrope', sans-serif; letter-spacing: .08em;}
.banner .nome {font: 900 2.6rem/0.95 'Archivo', sans-serif; color: #fff; margin: 10px 0 8px 0; letter-spacing: -.01em;}
.banner .nome span {color: #E02597; display: block;}
.banner .urna {display: inline-flex; align-items: center; gap: 10px; background: #fff; border-radius: 14px;
               padding: 6px 14px; box-shadow: 0 6px 20px rgba(0,0,0,.25);}
.banner .urna .vote {writing-mode: vertical-rl; transform: rotate(180deg); color: #E02597;
                     font: 800 .6rem 'Manrope', sans-serif; letter-spacing: .15em;}
.banner .urna .num {font: 900 2rem 'Archivo', sans-serif; color: #122545;}
.banner .urna .mdb {background: #E02597; color: #fff; border-radius: 8px; padding: 2px 8px;
                    font: 900 .8rem 'Manrope', sans-serif;}
.banner .sub {color: rgba(255,255,255,.85); font: 600 .95rem 'Manrope', sans-serif; margin-top: 10px;}
.banner .contagem {display: inline-block; margin-left: 8px; background: #E02597; color: #fff;
                   border-radius: 999px; padding: 4px 12px; font: 900 .72rem 'Manrope', sans-serif;}
/* foto inteira dentro do banner, com folga acima da cabeça */
.banner img {position: absolute; right: 3%; bottom: 0; height: calc(100% - 16px); max-height: 250px;
             width: auto; object-fit: contain; object-position: bottom; z-index: 1;}
/* ---------- celular e tablet ---------- */
@media (max-width: 760px) {
  .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 3.4rem;}
  .banner {display: flex; flex-direction: column; min-height: 0;}
  .banner .texto {max-width: 100%; padding: 18px 18px 0 18px;}
  .banner .selo {font-size: .6rem; padding: 3px 10px;}
  .banner .contagem {font-size: .62rem; margin: 6px 0 0 0;}
  .banner .nome {font-size: 2.1rem;}
  .banner .urna .num {font-size: 1.6rem;}
  .banner .sub {font-size: .8rem;}
  /* foto inteira, abaixo do texto */
  .banner img {position: static; display: block; align-self: center; height: 210px; max-height: none;
               margin-top: 6px;}
  /* indicadores em grade 2 × 2 em vez de 4 blocos empilhados */
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {flex-wrap: wrap; gap: .6rem;}
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {
      flex: 1 1 calc(50% - .6rem) !important; min-width: calc(50% - .6rem) !important; width: auto !important;}
  [data-testid="stMetricValue"] {font-size: 1.35rem !important;}
  [data-testid="stMetricLabel"] p {font-size: .75rem;}
  [data-testid="stMetric"] {padding: 8px 10px;}
  .cartao {padding: 12px 14px;}
  .cartao h4 {font-size: 1.05rem;}
  h2, h3 {font-size: 1.3rem !important;}
  .rodape {flex-direction: column; text-align: center;}
}
@media (min-width: 761px) and (max-width: 1100px) {
  .banner .texto {max-width: 58%;}
  .banner .nome {font-size: 2.2rem;}
  .banner img {max-height: 220px;}
}
/* layout alternado: fúcsia suave × azul suave sobre fundo quase branco */
[data-testid="stMetric"] {border-radius: 14px; padding: 10px 14px; box-shadow: 0 2px 8px rgba(18,37,69,.05);
                          background: #FDEFF7; border: 1px solid #F2C4DE;}
[data-testid="stColumn"]:nth-child(even) [data-testid="stMetric"] {background: #EDF3FC; border-color: #C8DAF3;}
[data-testid="stPlotlyChart"] {background: #FFFFFF; border: 1px solid #F2C4DE; border-top: 4px solid #E02597;
                               border-radius: 14px; padding: 6px; box-shadow: 0 2px 8px rgba(224,37,151,.06);}
[data-testid="stDataFrame"] {background: #FFFFFF; border: 1px solid #C8DAF3; border-top: 4px solid #6D93D1;
                             border-radius: 14px; padding: 6px; box-shadow: 0 2px 8px rgba(18,37,69,.06);}
[data-testid="stVerticalBlockBorderWrapper"] {background: #FFFFFF; border-color: #C8DAF3 !important;}
.stTabs [data-baseweb="tab-list"] {background: linear-gradient(90deg, #EDF3FC, #FDEFF7); border-radius: 12px;
                                   padding: 0 8px; border: 1px solid #E3D6EC;}
.cartao {box-shadow: 0 2px 8px rgba(18,37,69,.05);}
.cartao.alerta {background: #EDF3FC; border-left-color: #F2A900;}
.cartao.risco {background: #EDF3FC; border-left-color: #122545;}
.rodape {display: flex; align-items: center; gap: 16px; margin-top: 28px; padding: 14px 18px;
         border-radius: 16px; background: #FFFFFF; border: 1px solid #F2C4DE; color: #122545;}
.rodape img {height: 70px;}
</style>
""", unsafe_allow_html=True)


ZEBRA_AZUL, ZEBRA_BRANCO = "#EAF1FB", "#FFFFFF"


def _fmt_numero(casas):
    def f(v):
        if pd.isna(v):
            return ""
        return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f


def tabela(df, **kwargs):
    """st.dataframe com linhas alternadas em azul claro e números no padrão brasileiro."""
    kwargs.pop("column_config", None)  # a formatação passa a ser feita pelo Styler
    df = df.reset_index(drop=True)
    formatos = {}
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c]):
            decimal = any(t in str(c) for t in ("%", "por seção", "Km"))
            formatos[c] = _fmt_numero(1 if decimal else 0)
    estilo = (df.style.format(formatos)
              .apply(lambda linha: [f"background-color: {ZEBRA_AZUL if linha.name % 2 else ZEBRA_BRANCO}"]
                     * len(linha), axis=1))
    kwargs.setdefault("hide_index", True)
    kwargs.setdefault("width", "stretch")
    return st.dataframe(estilo, **kwargs)


@st.cache_data
def foto_base64():
    return base64.b64encode(FOTO.read_bytes()).decode() if FOTO.exists() else ""


def n(x):
    """Número no padrão brasileiro."""
    return f"{x:,.0f}".replace(",", ".")


def mil(x):
    """Formato curto: 53,4 mil."""
    return f"{x / 1000:.1f} mil".replace(".", ",")


def pct(x):
    return f"{100 * x:.0f}%"


@st.cache_data
def carregar():
    base = pd.read_csv(PASTA / "previsao_v13_municipios.csv")
    base["situacao_campo"] = base["situacao_campo"].fillna("Sem campo e sem histórico")
    resumo = json.load(open(PASTA / "resumo_v13.json", encoding="utf-8"))
    agenda = pd.read_csv(PASTA / "agenda_v13.csv")
    lid = pd.read_csv(PASTA / "liderancas_v13.csv")
    geo = json.load(open(PASTA / "ma_municipios_leve.geojson", encoding="utf-8"))
    tb = pd.read_csv(PASTA / "tuntum_bairros_v13.csv")
    ts = pd.read_csv(PASTA / "tuntum_secoes_v13.csv")
    ps = pd.read_csv(PASTA / "projecao_secoes_v13.csv")
    ps["bairro"] = ps["bairro"].fillna("")
    return base, resumo, agenda, lid, geo, tb, ts, ps


base, R, agenda, lid, geo, tun_bairros, tun_secoes, proj_secoes = carregar()
TUN = R["tuntum"]
IDX_TUNTUM = int(np.flatnonzero(base.cidade_norm.values == "tuntum")[0])
base["cd_ibge"] = base["cd_ibge"].astype(str)
sim = R["simulacao"]
ref = R["referencias"]
dias_restantes = (ELEICAO - pd.Timestamp.today().normalize()).days


# ----------------------------------------------------------------------
# Projeção (mesma lógica de modelos_v13.py) — usada no simulador
# ----------------------------------------------------------------------
def projetar(df, taxa_transf, taxa_rec, taxa_campo, cresc, choque=1.0, conv_tuntum=None, choque_tuntum=1.0):
    eleitores = df["total_dep_est_2022"].values * (1 + cresc)
    sobrep = df["pct_sobreposicao"].values / 100
    extra_2018 = np.clip(df["pct_fernando_pessoa_2018"].values / 100 - sobrep, 0, None)
    hist = eleitores * (taxa_transf * sobrep + taxa_rec * extra_2018)
    campo = df["expectativa_total"].values * taxa_campo
    total = np.array((np.maximum(hist, campo) + 0.2 * np.minimum(hist, campo)) * choque, dtype=float)
    if conv_tuntum is not None:  # Tuntum usa a calibração por seção (voto do prefeito 2024)
        valor = TUN["fernando_2024"] * conv_tuntum * np.ravel(choque_tuntum)
        if total.ndim == 1:
            total[IDX_TUNTUM] = valor[0]
        else:
            total[:, IDX_TUNTUM] = valor
    return total


def liderancas_de(cidade_norm):
    nomes = lid.loc[lid.cidade_norm == cidade_norm, "lideranca"].dropna().tolist()
    return [x for x in nomes if x and x.lower() != "nan"]


def ficha_texto(m):
    """Leitura em linguagem natural de um município."""
    partes = []
    onde = ("é a cidade-base da Bruna" if m.cidade_norm == "tuntum"
            else f"fica a {n(m.dist_tuntum_km)} km de Tuntum")
    partes.append(
        f"**{m.municipio}** (região de {m.regiao_imediata}) {onde} e teve "
        f"{n(m.total_dep_est_2022)} votos para deputado estadual em 2022.")
    if m.cidade_norm == "tuntum":
        partes.append(
            f"Aqui a projeção usa a calibração **seção por seção** (voto do Fernando para prefeito em 2024 × "
            f"conversão observada em 2022) — veja a aba **Tuntum** para o detalhe por bairro.")
    hist = []
    if m.fernando_pessoa_2018 > 0:
        hist.append(f"Fernando Pessoa fez {n(m.fernando_pessoa_2018)} votos aqui em 2018 ({m.pct_fernando_pessoa_2018:.1f}%)")
    if m.eric_costa_2022 > 0:
        hist.append(f"Eric Costa fez {n(m.eric_costa_2022)} em 2022 ({m.pct_eric_costa_2022:.1f}%)")
    if m.abigail_2022 > 0:
        hist.append(f"Abigail fez {n(m.abigail_2022)} ({m.pct_abigail_2022:.1f}%)")
    if m.daniella_2022 > 0:
        hist.append(f"Daniella fez {n(m.daniella_2022)} ({m.pct_daniella_2022:.1f}%)")
    if hist:
        partes.append("No histórico: " + "; ".join(hist) + ".")
    if m.votos_fieis_grupo > 0:
        partes.append(
            f"Cerca de **{n(m.votos_fieis_grupo)} eleitores acompanharam o grupo Pessoa nas duas últimas eleições** "
            f"— em 2022 esse voto foi para o Eric. A tarefa aqui é avisar que agora o voto é Bruna: "
            f"estimamos ~{n(m.eleitor_eric_a_converter)} ainda não convertidos.")
    if m.tem_campo:
        nomes = liderancas_de(m.cidade_norm)
        quem = f" ({', '.join(nomes[:6])}{'…' if len(nomes) > 6 else ''})" if nomes else ""
        partes.append(
            f"A equipe de campo tem {int(m.total_liderancas)} liderança(s){quem} com expectativa de "
            f"{n(m.expectativa_total)} votos. O prefeito {'**apoia**' if m.prefeito_apoia else 'não está no grupo'}.")
    else:
        partes.append("Não há liderança cadastrada na planilha de campo.")
    partes.append(
        f"**Projeção do modelo: {n(m.votos_projetados)} votos** (faixa provável de {n(m.votos_p10)} a {n(m.votos_p90)}).")
    sit = {
        "Cobrar e confirmar": "⚠️ A expectativa das lideranças está muito acima do que a história da região sustenta. "
                              "Ligar hoje, confirmar quem são os cabos eleitorais e o transporte no domingo.",
        "Base confirmada pela história": "✅ O histórico confirma a expectativa da equipe. Manter e blindar.",
        "Voto sem liderança: nomear responsável": "📌 Há voto histórico do grupo aqui, mas nenhuma liderança cadastrada. "
                                                  "Nomear um responsável ainda esta semana.",
        "Acompanhar": "Acompanhar a rede local; sem sinal de alerta.",
    }.get(m.situacao_campo, "")
    if sit:
        partes.append(sit)
    partes.append(f"**Perfil: {m.segmento}.** {m.acao_segmento}")
    return "\n\n".join(partes)


# ----------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------
_foto = foto_base64()
_img = f'<img src="data:image/png;base64,{_foto}" alt="Bruna Pessoa">' if _foto else ""
_faltam = max(dias_restantes, 0)
st.markdown(f"""
<div class="banner">
  <div class="texto">
    <div class="selo">ESTRATÉGIA DA RETA FINAL · USO INTERNO</div><span class="contagem">{"É HOJE" if _faltam == 0 else f"FALTAM {_faltam} DIAS"}</span>
    <div class="nome">BRUNA<span>PESSOA</span></div>
    <div class="urna"><span class="vote">VOTE</span><span class="num">15800</span><span class="mdb">MDB</span></div>
    <div class="sub">Deputada Estadual · Maranhão — TSE 2018/2022, Tuntum seção a seção, rede de lideranças e
    modelos de previsão · atualizado em 27/09/2026</div>
  </div>
  {_img}
</div>
""", unsafe_allow_html=True)

abas = st.tabs(["📋 Resumo da semana", "🗓️ Agenda", "📞 Lideranças", "🏠 Tuntum", "🧮 Seções e bairros",
                "🔁 Eleitor do Eric", "🗺️ Mapa",
                "🗳️ Dia da eleição", "🔎 Município", "🎛️ Simulador", "💬 Pergunte à estratégia",
                "ℹ️ Como funciona"])

# ----------------------------------------------------------------------
# 1. Resumo
# ----------------------------------------------------------------------
with abas[0]:
    k = st.columns(4)
    k[0].metric("Projeção central", mil(sim["p50"]) + " votos")
    k[1].metric("Faixa provável (80%)", f"{mil(sim['p10'])} a {mil(sim['p90'])}")
    k[2].metric("Chance de superar 38,3 mil", pct(sim["prob_acima"]["ultimo_eleito_chapa_governo_2022"]),
                help="Votação do último eleito da chapa do governo (PSB) em 2022")
    k[3].metric("Votos que seguiram o grupo", n(R["votos_fieis_grupo_total"]),
                help="Eleitores que votaram no candidato apoiado pelo grupo Pessoa em 2018 e em 2022")

    st.subheader("O que os números dizem")
    sit = R["situacao_campo"]
    sens = R["sensibilidade"]
    maior_risco = max(sens, key=sens.get)
    st.markdown(f"""
<div class="cartao"><h4>1. A candidatura é competitiva</h4>
Em 20 mil cenários simulados, a Bruna fica entre <b>{n(sim['p10'])}</b> e <b>{n(sim['p90'])}</b> votos em 80% dos casos,
com centro em <b>{n(sim['p50'])}</b>. Em 2022 o último eleito da chapa do governo teve 38,3 mil e a mediana dos
42 eleitos foi {n(ref['mediana_eleitos_2022'])}. Os números sustentam a eleição, <b>se a rede entregar</b>.</div>

<div class="cartao alerta"><h4>2. O maior risco é a entrega das lideranças, não o adversário</h4>
A variável que mais move o resultado é <b>{maior_risco.lower()}</b> (correlação de {sens[maior_risco]:.2f} com o total).
Em <b>{sit.get('Cobrar e confirmar', 0)} municípios</b> a expectativa da equipe está bem acima do que a história
sustenta — somam ~{n(R['votos_campo_sem_historico'])} votos projetados. É aqui que a semana se ganha ou se perde:
ligar, confirmar nomes, transporte e fiscal.</div>

<div class="cartao"><h4>3. Tuntum: entre {mil(TUN['bruna']['conservador'])} e {mil(TUN['bruna']['forte'])} votos</h4>
Medido seção a seção: em 2022 o grupo Pessoa converteu <b>{pct(TUN['conversao']['conservador'])}</b> do voto do
prefeito em voto para o Eric (candidato de fora); o grupo Tema converteu <b>{pct(TUN['conversao']['forte'])}</b> para
o Cleomar Tema (candidato da terra). A Bruna, da terra, deve ficar nessa faixa, com centro em
<b>{mil(TUN['bruna']['realista'])}</b>. Na região, ~{n(R['eleitor_eric_a_converter_total'])} eleitores ainda podem
votar no Eric por hábito. Mensagem: <i>"o Fernando agora é Bruna"</i>.</div>

<div class="cartao risco"><h4>4. Barra do Corda é o campo de batalha</h4>
Maior colégio da região: Fernando fez 36% em 2018, Abigail fez 42% em 2022 e Eric é ex-prefeito.
Projeção de <b>{n(base.loc[base.municipio == 'Barra do Corda', 'votos_projetados'].iloc[0])}</b> votos com a maior
incerteza do mapa — é onde uma visita vale mais.</div>
""", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        bordas = np.array(sim["bordas"])
        centros = (bordas[:-1] + bordas[1:]) / 2
        fig = go.Figure(go.Bar(x=centros, y=sim["histograma"], marker_color=ROSA, opacity=.85, name="Cenários",
                               showlegend=False, hovertemplate="%{x:,.0f} votos<extra></extra>"))
        topo = max(sim["histograma"]) * 1.05
        for nome, valor, cor in [
                ("Menor eleito 2022", ref["menor_eleito_2022"], CINZA),
                ("Último eleito da chapa do governo 2022", ref["ultimo_eleito_chapa_governo_2022"], AMARELO),
                ("Mediana dos eleitos 2022", ref["mediana_eleitos_2022"], MARINHO)]:
            # linha de referência como item de legenda (legível também no celular)
            fig.add_scatter(x=[valor, valor], y=[0, topo], mode="lines", name=f"{nome}: {mil(valor)}",
                            line=dict(color=cor, dash="dash", width=2), hoverinfo="name")
        fig.update_xaxes(range=[min(bordas[0], ref["menor_eleito_2022"]) * 0.95, bordas[-1]])
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.28, x=0, font=dict(size=11)))
        fig.update_layout(title="Distribuição dos 20 mil cenários simulados", height=440,
                          xaxis_title="Votos totais da Bruna", yaxis_title="Cenários", bargap=.05,
                          margin=dict(t=60, b=120, l=40, r=10))
        st.plotly_chart(fig, width="stretch")
    with col_b:
        st.markdown("**Adversários diretos na região**")
        adv = pd.DataFrame([{"Candidato": k2, "Votos 2022": n(v["votos_2022"]) if v["votos_2022"] else "—",
                             "Estimativa 2026": n(v["estimativa_2026"]) if v["estimativa_2026"] else "sem histórico",
                             "Leitura": v["nota"]}
                            for k2, v in R["adversarios"].items()])
        tabela(adv, hide_index=True, width="stretch")
        st.caption("Estimativa 2026 = votação 2022 ajustada pelo crescimento do eleitorado; para o Eric, "
                   "descontado o voto do grupo Pessoa. César Ferro não tem histórico para deputado estadual.")

    st.markdown("**Onde estão os votos, por perfil de município**")
    seg = pd.DataFrame(R["segmentos"]).rename(columns={
        "segmento": "Perfil", "municipios": "Municípios", "votos_projetados": "Votos projetados",
        "eleitores": "Eleitorado", "acao": "O que fazer"})
    tabela(seg, hide_index=True, width="stretch",
                 column_config={"Votos projetados": st.column_config.NumberColumn(format="localized"),
                                "Eleitorado": st.column_config.NumberColumn(format="localized")})

# ----------------------------------------------------------------------
# 2. Agenda
# ----------------------------------------------------------------------
with abas[1]:
    st.subheader("Agenda sugerida · 28/09 a 03/10")
    st.markdown(
        "Montada para **maximizar votos por hora de estrada**, saindo de Tuntum. O ganho estimado de cada parada "
        "combina: votos ainda indefinidos no município, eleitor do Eric a converter e força da rede local "
        "(em dobro onde o prefeito apoia). Paradas com ganho abaixo de 100 votos foram descartadas.")
    st.info("⚖️ Prazos legais (confirme com a assessoria jurídica): comícios e reuniões públicas até **quinta, 01/10**; "
            "caminhada, carreata e distribuição de material até **sábado, 03/10, às 22h**.")
    for dia, bloco in agenda.groupby("dia", sort=False):
        with st.container(border=True):
            st.markdown(f"#### {dia} · {bloco.tipo_ato.iloc[0]}")
            for _, a in bloco.iterrows():
                m = base.loc[base.municipio == a.municipio].iloc[0]
                motivo = []
                if m.eleitor_eric_a_converter >= 50:
                    motivo.append(f"~{n(m.eleitor_eric_a_converter)} eleitores do Eric a converter")
                if m.votos_em_jogo > 0:
                    motivo.append(f"{n(m.votos_em_jogo)} votos de incerteza")
                if m.tem_campo:
                    motivo.append(f"rede de {int(m.total_liderancas)} liderança(s)"
                                  + (", prefeito apoia" if m.prefeito_apoia else ""))
                st.markdown(f"**{a.ordem}. {a.municipio}** — +{n(a.ganho_estimado_votos)} votos estimados · "
                            f"{a.horas_deslocamento} h de estrada · _{a.segmento}_  \n"
                            f"<span class='pequeno'>Por quê: {'; '.join(motivo)}.</span>", unsafe_allow_html=True)
    st.metric("Ganho total estimado da agenda", n(R["ganho_agenda_total"]) + " votos")

    rota = agenda.merge(base[["municipio", "lat", "lon"]], on="municipio")
    rota["rotulo"] = rota.dia + " · " + rota.municipio
    fig = px.line_map(rota, lat="lat", lon="lon", color="dia", hover_name="rotulo", zoom=6,
                      center={"lat": rota.lat.mean(), "lon": rota.lon.mean()}, height=520,
                      map_style="carto-positron")
    fig.update_traces(mode="lines+markers", marker=dict(size=11))
    fig.update_layout(margin=dict(t=10, b=0, l=0, r=0), legend_title_text="")
    st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------------
# 3. Lideranças
# ----------------------------------------------------------------------
with abas[2]:
    st.subheader("Quem ligar hoje")
    st.markdown(
        "Comparamos a **expectativa que a equipe registrou** para cada município com o que o **histórico do TSE** "
        "sustenta. Onde a promessa está muito acima da história, não quer dizer que é falsa — quer dizer que "
        "**precisa ser confirmada nesta semana**: nomes dos cabos eleitorais, transporte, fiscais e material.")
    c = st.columns(3)
    cobrar = base[base.situacao_campo == "Cobrar e confirmar"].sort_values("expectativa_total", ascending=False)
    confirmada = base[base.situacao_campo == "Base confirmada pela história"].sort_values("votos_projetados", ascending=False)
    sem_lid = base[base.situacao_campo == "Voto sem liderança: nomear responsável"].sort_values("votos_historico", ascending=False)
    c[0].metric("⚠️ Cobrar e confirmar", f"{len(cobrar)} municípios", f"{n(cobrar.expectativa_total.sum())} votos prometidos", delta_color="off")
    c[1].metric("✅ Confirmados pela história", f"{len(confirmada)} municípios", f"{n(confirmada.votos_projetados.sum())} votos projetados", delta_color="off")
    c[2].metric("📌 Voto sem liderança", f"{len(sem_lid)} municípios", f"{n(sem_lid.votos_historico.sum())} votos históricos", delta_color="off")

    def com_nomes(df):
        out = df[["municipio", "expectativa_total", "votos_historico", "votos_projetados", "prefeito_apoia"]].copy()
        out["liderancas"] = df.cidade_norm.map(lambda c2: ", ".join(liderancas_de(c2)))
        out["prefeito_apoia"] = out.prefeito_apoia.map({1: "sim", 0: "não"})
        return out.rename(columns={"municipio": "Município", "expectativa_total": "Expectativa da equipe",
                                   "votos_historico": "Sustentado pelo histórico", "votos_projetados": "Projeção",
                                   "prefeito_apoia": "Prefeito apoia", "liderancas": "Lideranças"})

    cfg = {x: st.column_config.NumberColumn(format="localized")
           for x in ["Expectativa da equipe", "Sustentado pelo histórico", "Projeção"]}
    st.markdown("##### ⚠️ Cobrar e confirmar")
    tabela(com_nomes(cobrar), hide_index=True, width="stretch", column_config=cfg)
    st.markdown("##### 📌 Tem voto do grupo, mas ninguém cadastrado — nomear responsável")
    tabela(sem_lid[["municipio", "votos_historico", "votos_projetados", "dist_tuntum_km"]].rename(columns={
        "municipio": "Município", "votos_historico": "Votos históricos do grupo", "votos_projetados": "Projeção",
        "dist_tuntum_km": "Km de Tuntum"}), hide_index=True, width="stretch")
    st.markdown("##### ✅ Base confirmada pela história — manter e blindar")
    tabela(com_nomes(confirmada), hide_index=True, width="stretch", column_config=cfg)

# ----------------------------------------------------------------------
# Tuntum — bairro a bairro
# ----------------------------------------------------------------------
with abas[3]:
    st.subheader("Tuntum, seção por seção")
    st.markdown(
        f"Cruzamos as **{TUN['secoes']} seções** da eleição de prefeito de 2024 (Fernando {n(TUN['fernando_2024'])} × "
        f"Tema {n(TUN['tema_2024'])}) com o voto para deputado estadual de 2022 nas mesmas seções. "
        f"Em 2022 o grupo Pessoa entregou **{pct(TUN['conversao']['conservador'])}** do seu voto ao Eric; "
        f"o grupo Tema entregou **{pct(TUN['conversao']['forte'])}** ao Cleomar Tema, que é da terra. "
        f"Candidato da casa converte mais, e a Bruna deve ficar nessa faixa.")
    k = st.columns(4)
    k[0].metric("Conservador (padrão Eric)", n(TUN["bruna"]["conservador"]))
    k[1].metric("Realista", n(TUN["bruna"]["realista"]))
    k[2].metric("Forte (padrão Tema)", n(TUN["bruna"]["forte"]))
    k[3].metric("Não seguiu o grupo em 2022", n(TUN["grupo_nao_convertido_2022"]),
                help="Votou no Fernando para prefeito em 2024, mas não no Eric em 2022 (mesma seção)")
    top = tun_bairros.sort_values("grupo_nao_convertido_2022", ascending=False)
    b1 = top.iloc[0]
    st.markdown(f"""
<div class="cartao alerta"><h4>Onde está o voto a buscar em Tuntum</h4>
<b>{b1.bairro.title()}</b> concentra {n(b1.grupo_nao_convertido_2022)} eleitores que votaram no Fernando mas não
seguiram a indicação do grupo em 2022. Em seguida vêm {", ".join(top.bairro.iloc[1:4].str.title())}.
Nesses bairros o trabalho é <b>porta a porta com as lideranças do bairro</b>, não comício.</div>
""", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_bar(y=tun_bairros.bairro, x=tun_bairros.bruna_realista, name="Bruna (realista)",
                orientation="h", marker_color=ROSA)
    fig.add_bar(y=tun_bairros.bairro, x=tun_bairros.grupo_nao_convertido_2022, name="Não seguiu o grupo em 2022",
                orientation="h", marker_color=AMARELO)
    fig.add_bar(y=tun_bairros.bairro, x=tun_bairros.cleomar_tema_2022, name="Cleomar Tema 2022",
                orientation="h", marker_color=VERMELHO, opacity=.6)
    fig.update_layout(barmode="group", height=760, yaxis=dict(autorange="reversed", title=""),
                      xaxis_title="Votos", legend=dict(orientation="h", y=1.03), margin=dict(t=30, l=10))
    st.plotly_chart(fig, width="stretch")
    st.markdown("**Bairros**")
    tabela(tun_bairros.rename(columns={
        "bairro": "Bairro", "secoes": "Seções", "aptos_2024": "Eleitores aptos", "fernando_2024": "Fernando 2024",
        "tema_2024": "Tema 2024", "pct_fernando_2024": "% Fernando", "eric_2022": "Eric 2022",
        "cleomar_tema_2022": "Cleomar Tema 2022", "bruna_conservador": "Bruna conservador",
        "bruna_realista": "Bruna realista", "bruna_forte": "Bruna forte",
        "grupo_nao_convertido_2022": "Não seguiu o grupo 2022"}), hide_index=True, width="stretch")
    with st.expander("Ver todas as seções"):
        tabela(tun_secoes[["secao_txt", "local", "bairro", "aptos_2024", "fernando_2024", "tema_2024",
                                 "eric", "cleomar_tema", "bruna_realista", "grupo_nao_convertido_2022"]].rename(columns={
            "secao_txt": "Seção", "local": "Local", "bairro": "Bairro", "aptos_2024": "Aptos",
            "fernando_2024": "Fernando 2024", "tema_2024": "Tema 2024", "eric": "Eric 2022",
            "cleomar_tema": "Cleomar 2022", "bruna_realista": "Bruna realista",
            "grupo_nao_convertido_2022": "Não seguiu 2022"}), hide_index=True, width="stretch")

# ----------------------------------------------------------------------
# Seções e bairros — projeção de votos por seção eleitoral
# ----------------------------------------------------------------------
with abas[4]:
    st.subheader("Projeção de votos por seção e bairro")
    st.markdown(
        "Quantos votos a Bruna deve ter em **cada seção eleitoral**. Serve para dar **meta por seção** às lideranças "
        "e decidir onde colocar fiscal no domingo. Em **Tuntum** a projeção vem do voto do prefeito Fernando em 2024 "
        "(seção a seção) e é agrupada por **bairro**. Nos demais municípios, a projeção da cidade é distribuída entre "
        "as seções conforme onde o grupo teve voto (Fernando 2018 e Eric 2022) e agrupada por **local de votação**.")
    municipios_sec = (proj_secoes.groupby("municipio").bruna_projetados.sum()
                      .sort_values(ascending=False).index.tolist())
    c = st.columns([2, 2, 1])
    mun = c[0].selectbox("Município", municipios_sec, key="mun_secoes")
    ps = proj_secoes[proj_secoes.municipio == mun].copy()
    agrupar = "bairro" if (ps.bairro != "").any() else "local_votacao"
    rotulo = "Bairro" if agrupar == "bairro" else "Local de votação"
    filtro = c[1].selectbox(f"Filtrar {rotulo.lower()}", ["Todos"] + sorted(ps[agrupar].dropna().unique()),
                            key=f"filtro_secoes_{mun}")
    cenario = c[2].radio("Cenário", ["Realista", "Conservador", "Forte"], key="cen_secoes")
    col_cen = {"Realista": "bruna_projetados", "Conservador": "bruna_p10", "Forte": "bruna_p90"}[cenario]
    if filtro != "Todos":
        ps = ps[ps[agrupar] == filtro]

    k = st.columns(4)
    k[0].metric("Seções", len(ps))
    k[1].metric(f"Votos projetados ({cenario.lower()})", n(ps[col_cen].sum()))
    faixa = (f"{mil(ps.bruna_p10.sum())} a {mil(ps.bruna_p90.sum())}" if ps.bruna_p90.sum() >= 1000
             else f"{n(ps.bruna_p10.sum())} a {n(ps.bruna_p90.sum())}")
    k[2].metric("Faixa provável", faixa)
    k[3].metric("Votantes (base)", n(ps.votos_dep_est_2022.sum()),
                help="Tuntum: comparecimento 2024; demais: votos para dep. estadual em 2022")

    grp = (ps.groupby(agrupar)
           .agg(secoes=("secao", "count"), votantes=("votos_dep_est_2022", "sum"),
                projecao=(col_cen, "sum"), p10=("bruna_p10", "sum"), p90=("bruna_p90", "sum"))
           .reset_index().sort_values("projecao", ascending=False))
    grp["pct"] = (100 * grp.projecao / grp.votantes).round(1)
    fig = px.bar(grp.head(25), x="projecao", y=agrupar, orientation="h", color="pct",
                 color_continuous_scale=ESCALA_ROSA, text_auto=",.0f", height=max(320, 26 * min(len(grp), 25)),
                 labels={"projecao": "Votos projetados", agrupar: "", "pct": "% dos votantes"})
    fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=10, l=10))
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"**Por {rotulo.lower()}**")
    tabela(grp.rename(columns={agrupar: rotulo, "secoes": "Seções", "votantes": "Votantes",
                                     "projecao": "Projeção", "p10": "Mínimo provável", "p90": "Máximo provável",
                                     "pct": "% dos votantes"}),
                 hide_index=True, width="stretch",
                 column_config={x: st.column_config.NumberColumn(format="%.0f")
                                for x in ["Projeção", "Mínimo provável", "Máximo provável"]})

    st.markdown("**Seção a seção** · meta para lideranças e fiscais")
    ps["meta_secao"] = np.ceil(ps[col_cen]).astype(int)
    cols = ["secao_txt", "bairro", "local_votacao", "endereco", "votos_dep_est_2022", "fernando_2018",
            "eric_2022", "fernando_prefeito_2024", "tema_prefeito_2024", "meta_secao", "bruna_p10", "bruna_p90",
            "pct_bruna_estimado"]
    tab_secoes = ps.sort_values(col_cen, ascending=False)[cols].rename(columns={
        "secao_txt": "Seção", "bairro": "Bairro", "local_votacao": "Local de votação", "endereco": "Endereço",
        "votos_dep_est_2022": "Votantes", "fernando_2018": "Fernando 2018", "eric_2022": "Eric 2022",
        "fernando_prefeito_2024": "Fernando prefeito 2024", "tema_prefeito_2024": "Tema prefeito 2024",
        "meta_secao": "Meta Bruna", "bruna_p10": "Mínimo", "bruna_p90": "Máximo", "pct_bruna_estimado": "% estimado"})
    tab_secoes = tab_secoes.dropna(axis=1, how="all")
    if agrupar != "bairro":
        tab_secoes = tab_secoes.drop(columns=["Bairro"], errors="ignore")
    tabela(tab_secoes, hide_index=True, width="stretch",
                 column_config={x: st.column_config.NumberColumn(format="%.0f")
                                for x in ["Mínimo", "Máximo", "Fernando 2018", "Eric 2022"]})
    st.download_button("⬇️ Baixar metas por seção (CSV para Excel)",
                       tab_secoes.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"metas_secoes_{mun.lower().replace(' ', '_')}.csv", mime="text/csv")
    st.caption("A meta é uma estimativa estatística, não uma contagem. Use para priorizar: a seção com meta alta e "
               "sem fiscal é a primeira a cobrir. Fora de Tuntum, a divisão entre seções segue o histórico de 2018/2022 "
               "e pode mudar com a numeração de seções do TSE em 2026.")

# ----------------------------------------------------------------------
# 4. Eleitor do Eric
# ----------------------------------------------------------------------
with abas[5]:
    st.subheader("O eleitor que votou no Eric por causa do grupo")
    st.markdown(
        "Em 2022 o prefeito Fernando Pessoa apoiou Eric Costa. Parte desse eleitor votou **no grupo**, não no Eric. "
        "Medimos esse voto como a sobreposição entre o voto do Fernando em 2018 e o do Eric em 2022 "
        "(em Barra do Corda, terra do Eric, contamos só metade). Esse é o voto mais barato da campanha: "
        "já é do grupo, só precisa **saber que mudou**.")
    eric = base[base.votos_fieis_grupo > 0].sort_values("votos_fieis_grupo", ascending=False)
    k = st.columns(3)
    k[0].metric("Voto do grupo em jogo", n(eric.votos_fieis_grupo.sum()))
    k[1].metric("Ainda a converter (estimativa)", n(eric.eleitor_eric_a_converter.sum()))
    k[2].metric("Eric: perda estimada", n(R["adversarios"]["Eric Costa"]["votos_2022"] * 1.03
                                           - R["adversarios"]["Eric Costa"]["estimativa_2026"]))
    fig = px.bar(eric.head(15), x="municipio", y=["eleitor_eric_a_converter", "votos_fieis_grupo"],
                 barmode="overlay", color_discrete_sequence=[AMARELO, ROSA], height=380,
                 labels={"value": "Eleitores", "municipio": "", "variable": ""})
    fig.for_each_trace(lambda t: t.update(name={"eleitor_eric_a_converter": "A converter",
                                                "votos_fieis_grupo": "Voto do grupo"}[t.name]))
    fig.update_layout(margin=dict(t=20, b=40))
    st.plotly_chart(fig, width="stretch")
    st.markdown("**Ações de baixo custo para esta semana:** carro de som e santinho com a frase *\"Fernando agora é "
                "Bruna\"*; vídeo curto do prefeito pedindo voto na irmã; listas de transmissão de WhatsApp das "
                "lideranças que trabalharam para o Eric em 2022.")

# ----------------------------------------------------------------------
# 5. Mapa
# ----------------------------------------------------------------------
with abas[6]:
    visao = st.radio("Colorir o mapa por", ["Votos projetados", "Perfil estratégico", "Situação da rede de campo",
                                            "Voto do Eric 2022 (%)", "Voto da Abigail 2022 (%)"], horizontal=True)
    comum = dict(geojson=geo, locations="cd_ibge", featureidkey="properties.CD_MUN", hover_name="municipio",
                 map_style="carto-positron", zoom=5.3, center={"lat": -5.2, "lon": -45.2}, opacity=.75, height=640)
    hover = {"cd_ibge": False, "votos_projetados": ":,.0f", "segmento": True}
    if visao == "Votos projetados":
        fig = px.choropleth_map(base, color=np.log10(base.votos_projetados.clip(1)), hover_data=hover,
                                color_continuous_scale=ESCALA_ROSA, **comum)
        fig.update_coloraxes(colorbar=dict(title="Votos", tickvals=[1, 2, 3, 4], ticktext=["10", "100", "1 mil", "10 mil"]))
    elif visao == "Perfil estratégico":
        fig = px.choropleth_map(base, color="segmento", color_discrete_map=CORES_SEGMENTO, hover_data=hover, **comum)
    elif visao == "Situação da rede de campo":
        fig = px.choropleth_map(base, color="situacao_campo", hover_data=hover, color_discrete_map={
            "Cobrar e confirmar": AMARELO, "Base confirmada pela história": ROSA,
            "Voto sem liderança: nomear responsável": VERMELHO, "Acompanhar": "#7fb3d5",
            "Sem campo e sem histórico": "#eeeeee"}, **comum)
    else:
        col = "pct_eric_costa_2022" if "Eric" in visao else "pct_abigail_2022"
        fig = px.choropleth_map(base, color=col, hover_data=hover, color_continuous_scale="Reds",
                                range_color=(0, 40), **comum)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), legend_title_text="")
    st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------------
# 6. Dia da eleição
# ----------------------------------------------------------------------
with abas[7]:
    st.subheader("Domingo, 4 de outubro: onde colocar fiscais e mobilização")
    st.markdown(
        "Prioridade = votos projetados + metade da incerteza (onde o resultado ainda pode mudar). "
        "O número de seções e locais de votação vem do TSE (2022). **Votos por seção** mostra onde cada fiscal "
        "protege mais voto: acima de 30, vale fiscal em todas as seções; abaixo de 10, priorize os locais maiores.")
    dd = base.nlargest(25, "prioridade_dia_d").copy()
    dd["recomendacao"] = np.select(
        [dd.votos_por_secao >= 30, dd.votos_por_secao >= 10],
        ["Fiscal em todas as seções", "Fiscal por local de votação"], "Fiscal volante nos maiores locais")
    dd["fiscais_sugeridos"] = np.select(
        [dd.votos_por_secao >= 30, dd.votos_por_secao >= 10], [dd.secoes, dd.locais_votacao],
        np.ceil(dd.locais_votacao / 3)).astype(int)
    st.metric("Fiscais sugeridos (25 municípios prioritários)", n(dd.fiscais_sugeridos.sum()))
    tabela(dd[["municipio", "votos_projetados", "votos_em_jogo", "secoes", "locais_votacao",
                     "votos_por_secao", "recomendacao", "fiscais_sugeridos"]].rename(columns={
        "municipio": "Município", "votos_projetados": "Votos projetados", "votos_em_jogo": "Incerteza (votos)",
        "secoes": "Seções", "locais_votacao": "Locais de votação", "votos_por_secao": "Votos por seção",
        "recomendacao": "Recomendação", "fiscais_sugeridos": "Fiscais sugeridos"}),
        hide_index=True, width="stretch")
    st.caption("Transporte de eleitores no dia da eleição é crime eleitoral (Lei 6.091/74). "
               "Mobilização = lembrar, orientar e fiscalizar.")

# ----------------------------------------------------------------------
# 7. Ficha do município
# ----------------------------------------------------------------------
with abas[8]:
    ordem = base.sort_values("votos_projetados", ascending=False).municipio.tolist()
    escolha = st.selectbox("Escolha o município", ordem)
    m = base.loc[base.municipio == escolha].iloc[0]
    k = st.columns(4)
    k[0].metric("Projeção", n(m.votos_projetados))
    k[1].metric("Faixa provável", f"{n(m.votos_p10)} – {n(m.votos_p90)}")
    k[2].metric("Expectativa da equipe", n(m.expectativa_total))
    k[3].metric("Perfil", m.segmento)
    st.markdown(ficha_texto(m))
    comp = pd.DataFrame({
        "Candidato": ["Fernando Pessoa 2018", "Eric Costa 2022", "Abigail 2022", "Daniella 2022", "Bruna 2026 (projeção)"],
        "Votos": [m.fernando_pessoa_2018, m.eric_costa_2022, m.abigail_2022, m.daniella_2022, m.votos_projetados]})
    fig = px.bar(comp, x="Votos", y="Candidato", orientation="h", height=300, text_auto=",.0f",
                 color="Candidato", color_discrete_sequence=[MARINHO, AMARELO, VERMELHO, "#8e44ad", ROSA])
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10), yaxis_title="")
    st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------------
# 8. Simulador
# ----------------------------------------------------------------------
with abas[9]:
    st.subheader("E se…? Mexa nas premissas e veja o resultado")
    p = R["premissas"]
    c = st.columns(3)
    t1 = c[0].slider("Quanto do voto do grupo vem para a Bruna", 0.3, 1.0, p["taxa_transferencia"], .05,
                     help="Eleitor que seguiu o grupo em 2018 e 2022 (foi de Eric) e agora deve ir de Bruna")
    t2 = c[1].slider("Recuperação do eleitor do Fernando 2018", 0.0, 0.8, p["taxa_recuperacao_2018"], .05,
                     help="Quem votou no Fernando em 2018 mas não foi de Eric em 2022")
    t3 = c[2].slider("Quanto da expectativa das lideranças vira voto", 0.2, 1.0, p["taxa_realizacao_campo"], .05,
                     help="Equipes de campo costumam superestimar; 50% é uma premissa prudente")
    t4 = st.slider("Tuntum: quanto do voto do prefeito Fernando (2024) vira voto na Bruna", 0.5, 0.95,
                   float(p["conversao_tuntum"]), .01,
                   help=f"Eric (de fora) teve {pct(TUN['conversao']['conservador'])}; Cleomar Tema (da terra) "
                        f"teve {pct(TUN['conversao']['forte'])} do voto do seu grupo")
    total = projetar(base, t1, t2, t3, p["crescimento_eleitorado"], conv_tuntum=t4).sum()
    rng = np.random.default_rng(7)
    geral = rng.lognormal(-0.02, 0.12, (3000, 1))
    choques = geral * rng.lognormal(0, 0.25, (3000, len(base)))
    cen = projetar(base, t1, t2, t3, p["crescimento_eleitorado"], choque=choques,
                   conv_tuntum=t4, choque_tuntum=geral).sum(axis=1)
    k = st.columns(3)
    k[0].metric("Total projetado", mil(total), n(total - base.votos_projetados.sum()) + " vs. premissas-base")
    k[1].metric("Chance de superar 38,3 mil", pct((cen >= ref["ultimo_eleito_chapa_governo_2022"]).mean()))
    k[2].metric("Chance de superar 44 mil", pct((cen >= ref["mediana_eleitos_2022"]).mean()))
    st.markdown(
        f"Com essas premissas, a Bruna precisa que as lideranças entreguem pelo menos "
        f"**{pct(max(0, min(1, (ref['ultimo_eleito_chapa_governo_2022'] - projetar(base, t1, t2, 0, p['crescimento_eleitorado'], conv_tuntum=t4).sum()) / max(base.expectativa_total.sum(), 1))))}** "
        f"da expectativa registrada para chegar a 38,3 mil (cálculo aproximado).")

# ----------------------------------------------------------------------
# 9. Pergunte à estratégia (Claude)
# ----------------------------------------------------------------------
@st.cache_data
def contexto_para_ia():
    cols = ["municipio", "segmento", "votos_projetados", "votos_p10", "votos_p90", "expectativa_total",
            "votos_historico", "votos_fieis_grupo", "eleitor_eric_a_converter", "situacao_campo",
            "prefeito_apoia", "pct_fernando_pessoa_2018", "pct_eric_costa_2022", "pct_abigail_2022",
            "pct_daniella_2022", "dist_tuntum_km", "secoes", "locais_votacao"]
    tab = base[base.votos_projetados >= 50].sort_values("votos_projetados", ascending=False)[cols]
    lids = lid.groupby("cidade_norm").lideranca.apply(lambda s: ", ".join(map(str, s))).to_dict()
    tab["liderancas"] = base.loc[tab.index, "cidade_norm"].map(lids).fillna("")
    return (
        "RESUMO DOS MODELOS (JSON):\n" + json.dumps({k2: R[k2] for k2 in R if k2 != "simulacao"} | {
            "simulacao": {k2: v for k2, v in sim.items() if k2 not in ("histograma", "bordas")}},
            ensure_ascii=False) +
        "\n\nAGENDA SUGERIDA (CSV):\n" + agenda.to_csv(index=False) +
        "\n\nMUNICÍPIOS COM PROJEÇÃO >= 50 VOTOS (CSV):\n" + tab.to_csv(index=False))


SISTEMA = (
    "Você é o analista de estratégia da campanha de Bruna Pessoa (MDB), candidata a deputada estadual no "
    "Maranhão, apoiada pelo irmão, o prefeito de Tuntum Fernando Pessoa (que em 2022 apoiou Eric Costa). "
    "A eleição é no domingo, 4 de outubro de 2026. Responda em português do Brasil, de forma direta e prática, "
    "com foco no que a equipe consegue executar nos próximos dias (agenda, lideranças, mensagem, fiscais). "
    "Use apenas os dados fornecidos abaixo; quando algo não estiver nos dados, diga que não sabe. Cite números. "
    "Nunca sugira ações ilegais pela legislação eleitoral (compra de voto, transporte de eleitor no dia, "
    "propaganda fora do prazo).\n\n")

with abas[10]:
    st.subheader("Pergunte à estratégia")
    st.caption("Respostas geradas pelo Claude (Anthropic) com base somente nos dados deste painel.")
    tem_credencial = any(os.environ.get(v) for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"))
    if not tem_credencial:
        st.warning("Para ativar, defina a variável de ambiente `ANTHROPIC_API_KEY` antes de abrir o painel "
                   "(ou faça `ant auth login`) e recarregue a página.")
    sugestoes = ["Se a Bruna só pudesse ir a 3 cidades até quinta, quais e por quê?",
                 "Quais lideranças eu devo ligar hoje e o que perguntar a cada uma?",
                 "Qual a mensagem para o eleitor que votou no Eric em 2022 em Tuntum?",
                 "Onde estamos mais vulneráveis e o que fazer?"]
    if "chat" not in st.session_state:
        st.session_state.chat = []
    cols = st.columns(len(sugestoes))
    pergunta = None
    for i, s in enumerate(sugestoes):
        if cols[i].button(s, width="stretch"):
            pergunta = s
    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).markdown(msg["content"])
    pergunta = st.chat_input("Escreva sua pergunta…") or pergunta
    if pergunta:
        st.chat_message("user").markdown(pergunta)
        st.session_state.chat.append({"role": "user", "content": pergunta})
        with st.chat_message("assistant"):
            try:
                import anthropic
                cliente = anthropic.Anthropic()
                with cliente.beta.messages.stream(
                    model="claude-opus-5",
                    max_tokens=16000,
                    thinking={"type": "adaptive"},
                    output_config={"effort": "medium"},
                    system=[{"type": "text", "text": SISTEMA + contexto_para_ia(),
                             "cache_control": {"type": "ephemeral"}}],
                    messages=st.session_state.chat,
                    betas=["server-side-fallback-2026-07-01"],
                    extra_body={"fallbacks": "default"},
                ) as stream:
                    resposta = st.write_stream(stream.text_stream)
                    final = stream.get_final_message()
                if final.stop_reason == "refusal":
                    resposta = "Não consegui responder a essa pergunta. Tente reformular."
                    st.markdown(resposta)
                st.session_state.chat.append({"role": "assistant", "content": resposta or ""})
            except anthropic.AuthenticationError:
                st.error("Credencial da Anthropic inválida. Verifique a ANTHROPIC_API_KEY.")
                st.session_state.chat.pop()
            except anthropic.RateLimitError:
                st.error("Limite de uso atingido. Aguarde um minuto e tente de novo.")
                st.session_state.chat.pop()
            except anthropic.APIConnectionError:
                st.error("Sem conexão com a API. Verifique a internet.")
                st.session_state.chat.pop()
            except anthropic.APIStatusError as e:
                st.error(f"Erro da API ({e.status_code}): {e.message}")
                st.session_state.chat.pop()
            except TypeError:
                st.error("Nenhuma credencial da Anthropic encontrada. Defina ANTHROPIC_API_KEY.")
                st.session_state.chat.pop()

# ----------------------------------------------------------------------
# 10. Como funciona
# ----------------------------------------------------------------------
with abas[11]:
    mp = R["modelo_potencial"]
    st.subheader("Como o painel chega aos números")
    st.markdown(f"""
**Fontes.** Votação por seção do TSE de 2018 e 2022 (deputado estadual, Maranhão, 1º turno), agregada por município;
planilha de lideranças da campanha (`CIDADES ATUALIZADO.xlsx`); votação de prefeito de Tuntum 2024 por seção
e bairro (campanha); malha municipal do IBGE.

**Linha de corte.** Reconstruímos a distribuição das 42 cadeiras de 2022 pelo quociente eleitoral
({n(R['corte_2022']['quociente_eleitoral'])} votos) e sobras. A simulação acerta os eleitos conhecidos
(Abigail, Daniella e Eric). Menor eleito: {n(ref['menor_eleito_2022'])}; último eleito da chapa do governo (PSB): 38.329;
mediana: {n(ref['mediana_eleitos_2022'])}. Em 2026 a vaga depende da posição da Bruna **dentro da chapa do MDB**.

**Modelo 1 — Potencial do grupo (Gradient Boosting).** Aprende onde o grupo Pessoa tem voto (alvo: % do Fernando
em 2018) usando distância de Tuntum, porte, localização e o mapa de 2022. Validação cruzada: R² = {mp['r2_validacao_cruzada']},
erro médio de {mp['erro_medio_pontos_pct']} ponto percentual. A variável mais importante é a distância de Tuntum —
o voto do grupo é regional e cai rápido com a distância.

**Modelo 2 — Projeção por município.** Voto herdado (sobreposição Fernando 2018 × Eric 2022, × {pct(p['taxa_transferencia'])})
+ eleitor do Fernando 2018 recuperável (× {pct(p['taxa_recuperacao_2018'])}) — comparado com a expectativa das
lideranças (× {pct(p['taxa_realizacao_campo'])}). Vale o maior dos dois mais 20% do menor.

**Tuntum — calibração por seção.** Em Tuntum o modelo não usa a regra geral: usa as {TUN['secoes']} seções do
prefeito 2024 cruzadas com o deputado estadual 2022. Conversão observada do voto de prefeito em voto de deputado:
grupo Pessoa → Eric (de fora) {pct(TUN['conversao']['conservador'])}; grupo Tema → Cleomar Tema (da terra)
{pct(TUN['conversao']['forte'])}. A Bruna é simulada nessa faixa (centro {pct(TUN['conversao']['realista'])}).

**Modelo 3 — Monte Carlo.** 20 mil cenários variando as três taxas, um choque geral de campanha, choques regionais
e municipais. A faixa de 80% é o intervalo entre os percentis 10 e 90.

**Modelo 4 — Perfis (K-Means).** Agrupa os 217 municípios em 6 perfis pelo histórico dos quatro candidatos,
porte, distância e densidade da rede de campo.

**Modelo 5 — Agenda.** Escolhe, dia a dia, a próxima cidade com maior ganho de votos por hora (estrada + 2,5 h de ato),
respeitando 13 h de jornada e o encerramento em Tuntum no sábado.

**Limites — leia antes de decidir.**
- Não há pesquisa pública de intenção de voto para deputado estadual com esses nomes; o modelo usa histórico, não pesquisa.
- A Bruna nunca disputou; o Fernando (2018) é a melhor referência, mas não é a mesma candidatura.
- A expectativa das lideranças é a variável que mais pesa e a menos verificável. Por isso a aba **Lideranças** existe.
- Números de 2022 foram ajustados em +3% de eleitorado; César Ferro não tem histórico.
""")

# ----------------------------------------------------------------------
# Rodapé
# ----------------------------------------------------------------------
st.markdown(f"""
<div class="rodape">
  {_img}
  <div><b style="font-family:Archivo;font-size:1.1rem">Bruna Pessoa · 15800</b><br>
  <span class="pequeno">Painel de uso interno da coordenação. Não divulgar projeções, metas nem nomes de lideranças.</span></div>
</div>
""", unsafe_allow_html=True)
