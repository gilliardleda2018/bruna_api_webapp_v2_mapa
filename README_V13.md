# Painel Estratégico V13 — Bruna Pessoa (Dep. Estadual MA / MDB)

## Abrir o painel
Clique duas vezes em `iniciar_painel.bat` (abre em http://localhost:8513).

## Atualizar os números
Depois de atualizar a planilha de lideranças (`..\CIDADES ATUALIZADO.xlsx`), rode `atualizar_modelos.bat`.

## Pipeline
| Ordem | Script | O que faz |
|---|---|---|
| 1 | `..\dados_tse\agregar_votacao.py 2018` / `2022` | Agrega a votação por seção do TSE por município |
| 2 | `..\dados_tse\montar_base_rivais.py` | Votos de Bruna (Fernando 2018), Daniella, Abigail e Eric por município |
| 3 | `..\dados_tse\contar_secoes_2022.py` | Seções e locais de votação por município |
| 4 | `calcular_corte_2022.py` | Reconstrói as 42 cadeiras de 2022 e a linha de corte |
| 5 | `preparar_base_v13.py` | Junta TSE + planilha de campo + mapa IBGE |
| 6 | `tuntum_secoes_v13.py` | Calibra Tuntum seção a seção (prefeito 2024 × dep. estadual 2022) |
| 7 | `modelos_v13.py` | Modelo de potencial, projeção, Monte Carlo, perfis e agenda |
| 8 | `secoes_v13.py` | Projeção por seção eleitoral (bairro em Tuntum, local de votação nos demais) |
| 9 | `duelo_v13.py` | Clássico Tuntum × Barra do Corda: Bruna × Abigail por bairro, local e campo neutro |
| 10 | `duelo_modelos_v13.py` | Regressão de incumbência (Abigail 2026), classificação de seções e Monte Carlo do duelo |
| 11 | `dashboard_bruna_v13_estrategico.py` | Painel Streamlit |

## Aba "Pergunte à estratégia"
Usa o **Gemini** (Google) com chave gratuita criada em aistudio.google.com.
- No computador: `set GEMINI_API_KEY=sua-chave` antes de abrir o painel.
- No Streamlit Cloud: *Settings → Secrets* → `GEMINI_API_KEY = "sua-chave"`.
- `GEMINI_MODEL`: padrão `auto` (usa o Gemini Flash estável mais novo disponível na chave). Para fixar um
  modelo, informe o nome, por exemplo `gemini-2.5-pro`.

As respostas usam apenas os dados do painel. **No plano gratuito o Google pode usar as conversas para melhorar
os produtos dele**, por isso os nomes das lideranças não são enviados. Com uma chave de plano pago, defina
`GEMINI_PLANO_PAGO = "1"` para incluí-los.

## Publicar no Streamlit Community Cloud
1. Em share.streamlit.io → **Create app** → repositório `gilliardleda2018/bruna_api_webapp_v2_mapa`, branch `main`,
   arquivo principal `dashboard_bruna_v13_estrategico.py`.
2. **Mantenha o app privado**: o painel tem nomes de lideranças, metas e estratégia. Em *Settings → Sharing*,
   convide só a coordenação pelo e-mail.
3. Para a aba "Pergunte à estratégia": *Settings → Secrets* → `GEMINI_API_KEY = "sua-chave"`.
4. Para atualizar os números: rode `atualizar_modelos.bat` no computador, faça commit dos CSV/JSON e push —
   o app republica sozinho.

Os dados brutos do TSE (votação por seção, ~1 GB) **não** vão para o repositório; ficam em `C:\modelo_bruna\dados_tse`.

## Publicar no Render (versão em uso)
O link do Render é **público**: defina a senha de acesso antes de divulgar o endereço à coordenação.

*Environment → Environment Variables*:

| Variável | Valor |
|---|---|
| `APP_PASSWORD` | senha da coordenação (**obrigatória**: sem ela o painel abre para qualquer pessoa) |
| `GEMINI_API_KEY` | chave do Google AI Studio |
| `GEMINI_MODEL` | opcional, padrão `auto` |

O `render.yaml` já traz o comando de início, a versão do Python e a prévia do link no WhatsApp (`preparar_render.py`).
