"""Insere título e miniatura (Open Graph) no HTML do Streamlit antes de iniciar.

O WhatsApp (e Telegram, Instagram, etc.) monta a prévia do link lendo as tags
<meta property="og:..."> do HTML inicial, sem rodar JavaScript. O Streamlit
serve sempre o mesmo index.html com o título "Streamlit" e sem imagem, então
este script grava as tags nesse arquivo. Roda no início do Start Command.

A imagem fica em static/og-bruna.jpg (servida em /app/static/og-bruna.jpg,
graças a server.enableStaticServing no .streamlit/config.toml).
"""
import html
import os
import re
from pathlib import Path

import streamlit

TITULO = "Bruna Pessoa 15800 · Painel da Campanha"
DESCRICAO = "Deputada Estadual · Maranhão. Acesso restrito à coordenação."
MARCA = "<!-- og-bruna -->"

base = (os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("PUBLIC_URL") or "").rstrip("/")
indice = Path(streamlit.__file__).parent / "static" / "index.html"
texto = indice.read_text(encoding="utf-8")

# Remove uma inserção anterior (reinícios do serviço) antes de gravar de novo.
texto = re.sub(re.escape(MARCA) + r".*?" + re.escape(MARCA), "", texto, flags=re.S)

t, d = html.escape(TITULO), html.escape(DESCRICAO)
tags = [
    f'<meta property="og:title" content="{t}">',
    f'<meta property="og:description" content="{d}">',
    '<meta property="og:type" content="website">',
    '<meta property="og:locale" content="pt_BR">',
    f'<meta name="description" content="{d}">',
    '<meta name="twitter:card" content="summary_large_image">',
]
if base:
    img = f"{base}/app/static/og-bruna.jpg"
    tags += [
        f'<meta property="og:url" content="{base}/">',
        f'<meta property="og:image" content="{img}">',
        f'<meta property="og:image:secure_url" content="{img}">',
        '<meta property="og:image:type" content="image/jpeg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta name="twitter:image" content="{img}">',
    ]

texto = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", texto, count=1, flags=re.S)
# Depois do <meta charset> (precisa ficar no começo, senão os acentos quebram).
texto = texto.replace("</head>", MARCA + "".join(tags) + MARCA + "</head>", 1)
indice.write_text(texto, encoding="utf-8")
print(f"Open Graph gravado em {indice} (base: {base or 'sem URL — imagem omitida'})")
