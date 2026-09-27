@echo off
REM Recalcula base, Tuntum e modelos (rodar depois de atualizar a planilha CIDADES ATUALIZADO.xlsx).
cd /d "%~dp0"
python preparar_base_v13.py && python tuntum_secoes_v13.py && python modelos_v13.py && python secoes_v13.py && python duelo_v13.py && python duelo_modelos_v13.py
echo.
echo Modelos atualizados. Recarregue o painel no navegador.
pause
