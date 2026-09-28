@echo off
:: 激活当前目录下的 .venv 并运行 run.py
call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0run.py"
pause