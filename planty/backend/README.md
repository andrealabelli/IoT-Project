# Planty Backend

Backend FastAPI con JWT auth, bridge MQTT, storage telemetria e notifiche Telegram.

## Prerequisiti
- Python 3.11+

## Install (venv)
```bash
cd planty/backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

## Run
```bash
cd planty/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Test
```bash
cd planty/backend
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt && pytest -q
```

I test `test_auth.py` e `test_state.py` non dipendono da variabili env esterne: usano default settings e funzioni pure.
