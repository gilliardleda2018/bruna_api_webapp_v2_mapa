@echo off
REM Abre o Painel Estrategico V13 da Bruna Pessoa no navegador.
REM Para ativar a aba "Pergunte a estrategia", defina a chave antes:  set ANTHROPIC_API_KEY=sua-chave
cd /d "%~dp0"
python -m streamlit run dashboard_bruna_v13_estrategico.py --server.port 8513
