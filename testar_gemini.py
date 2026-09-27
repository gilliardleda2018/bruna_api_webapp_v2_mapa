"""Teste rápido da chave do Gemini, sem enviar nenhum dado da campanha.

Uso (PowerShell):
    $env:GEMINI_API_KEY = "sua-chave"
    python testar_gemini.py

Mostra os modelos que a chave enxerga, a ordem que o painel vai tentar e faz uma
pergunta neutra ("responda só: ok"). A chave nunca é impressa.
"""
import os
import re
import sys

from google import genai
from google.genai import errors, types

EXCLUIR = ("image", "tts", "audio", "live", "embedding", "aqa", "imagen", "veo", "learnlm", "robotics", "computer")


def nota(nome):  # mesma ordem usada pelo painel
    versao = re.search(r"(\d+(?:\.\d+)?)", nome)
    return ("flash" in nome, "gemini" in nome and "gemma" not in nome, "lite" not in nome,
            nome.endswith("latest"), not any(t in nome for t in ("preview", "exp")),
            float(versao.group(1)) if versao else 0.0)


chave = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not chave:
    sys.exit("Defina a chave antes:  $env:GEMINI_API_KEY = \"sua-chave\"")
print(f"Chave encontrada (termina em ...{chave[-4:]})")

cliente = genai.Client(api_key=chave)
try:
    nomes = [(m.name or "").split("/")[-1] for m in cliente.models.list()
             if not m.supported_actions or "generateContent" in m.supported_actions]
except errors.APIError as e:
    sys.exit(f"ERRO ao listar modelos ({e.code}): {e.message}")

texto = [n for n in nomes if not any(t in n for t in EXCLUIR)]
ordem = sorted(texto, key=nota, reverse=True)
print(f"\n{len(nomes)} modelos geram texto; o painel tentaria nesta ordem:")
for i, n in enumerate(ordem[:8], 1):
    print(f"  {i}. {n}")

for modelo in ordem[:6]:
    try:
        r = cliente.models.generate_content(model=modelo, contents="Responda só com a palavra: ok",
                                            config=types.GenerateContentConfig(
                                                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
        print(f"\nOK: {modelo} respondeu -> {(r.text or '').strip()[:40]!r}")
        break
    except errors.APIError as e:
        print(f"  {modelo}: erro {e.code} ({e.status})")
else:
    print("\nNenhum modelo respondeu. Envie esta saída para análise.")
