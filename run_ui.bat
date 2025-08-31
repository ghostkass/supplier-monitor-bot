@echo off
setlocal enabledelayedexpansion
title Supplier Monitor - UI

cd /d %~dp0

for %%D in (store scrapers notifiers utils) do (
  if not exist "%%D\__init__.py" type NUL > "%%D\__init__.py"
)

set "PYTHONPATH=%CD%"
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Virtualenv not found: %PY%
  echo Create it with:
  echo   python -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)

"%PY%" -m pip install --disable-pip-version-check --quiet streamlit==1.38.0 plotly==5.23.0

"%PY%" -c "from dotenv import load_dotenv; load_dotenv(); from store.db import Base, engine; Base.metadata.create_all(bind=engine); print('DB ready')"

"%PY%" -m streamlit run ui\app.py
