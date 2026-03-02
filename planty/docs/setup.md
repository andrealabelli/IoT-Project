# Setup end-to-end

## 1) Configurazione centralizzata `.env`
- Copia `planty/.env.example` in `planty/.env` (oppure copia root `.env.example` in root `.env`).
- Valori importanti:
  - Mosquitto MQTT: `1883`
  - Backend API: `8000`
  - Frontend: `5173`
  - Frontend endpoints: `VITE_API_URL`, `VITE_WS_URL`
- Copia firmware secrets/config:
  - `planty/firmware/arduino_uno/include/config.example.h` -> `config.h`
  - `planty/firmware/esp8266_bridge/include/secrets.example.h` -> `secrets.h`

## 2) Avvio stack
```bash
cd planty/infra
docker compose --env-file ../.env up --build
```

URL default:
- Mosquitto MQTT: `mqtt://localhost:1883`
- Backend: `http://localhost:8000` (`/health`, `/docs`)
- Frontend: `http://localhost:5173`

## 3) Flash firmware
- UNO: carica `planty/firmware/arduino_uno/src/main.ino`
- ESP8266: carica `planty/firmware/esp8266_bridge/src/main.ino`
- Collega UART UNO<->ESP con GND comune.

## 4) Test rapido MQTT senza device
Telemetria simulata:
```bash
mosquitto_pub -h localhost -t planty/plant-uno-01/telemetry -m '{"ts":"2026-01-10T10:20:00Z","t_c":23.1,"rh":44.0,"soil_pct":25,"state":"NEEDS_WATER","flags":["OK"]}'
```
Ack simulato:
```bash
mosquitto_pub -h localhost -t planty/plant-uno-01/ack -m '{"ts":"2026-01-10T10:20:02Z","cmd":"IRRIGATE","cmd_id":"sim-1","result":"OK"}'
```

## 5) Robustezza compose
- Tutti i servizi usano `restart: unless-stopped`
- `healthcheck` su Mosquitto e Backend
- `depends_on` con `condition: service_healthy`
- Backend MQTT con retry automatico in caso broker non pronto.

## 6) E2E senza hardware
Questa procedura valida il flusso completo backend + broker + dashboard senza Arduino/ESP.

### 6.1 Avvia docker compose
```bash
cd planty/infra
docker compose --env-file ../.env up --build
```

### 6.2 Register/Login via curl
```bash
# Register admin
curl -sS -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@planty.local","password":"Admin123!","role":"admin"}'

# Login
curl -sS -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@planty.local","password":"Admin123!"}'
```

Estrai token in shell:
```bash
TOKEN=$(curl -sS -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@planty.local","password":"Admin123!"}' | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### 6.3 Crea device via API
```bash
curl -sS -X POST http://localhost:8000/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"plant-uno-01","name":"Basilico","location":"Cucina"}'
```

### 6.4 Simula telemetria con mosquitto_pub
Payload conforme su `planty/<deviceId>/telemetry`:
```bash
mosquitto_pub -h localhost -p 1883 -t planty/plant-uno-01/telemetry -m '{"ts":"2026-01-10T10:20:00Z","t_c":23.1,"rh":45.2,"soil_pct":31,"state":"NEEDS_WATER","flags":["OK"]}'
```

Verifica latest dal backend:
```bash
curl -sS -X GET http://localhost:8000/devices/plant-uno-01/latest \
  -H "Authorization: Bearer $TOKEN"
```

### 6.5 Verifica update WebSocket backend
Opzione A (dashboard):
- Apri `http://localhost:5173`, fai login e apri il device `plant-uno-01`.
- Ripeti `mosquitto_pub` telemetry e verifica aggiornamento live (entro ~2s).

Opzione B (WS raw con Python):
```bash
python - <<'PY'
import asyncio, websockets

async def main():
    uri = "ws://localhost:8000/ws/plant-uno-01"
    async with websockets.connect(uri) as ws:
        await ws.send("keepalive")
        print(await ws.recv())

asyncio.run(main())
PY
```

### 6.6 Invia comando irrigate via API e verifica topic cmd
In terminale 1, sottoscrivi il topic comando:
```bash
mosquitto_sub -h localhost -p 1883 -t planty/plant-uno-01/cmd/irrigate -v
```

In terminale 2, invia comando:
```bash
curl -sS -X POST http://localhost:8000/devices/plant-uno-01/irrigate \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"duration_seconds":5}'
```

Devi vedere il payload pubblicato su `planty/plant-uno-01/cmd/irrigate` nel terminale `mosquitto_sub`.

### 6.7 Simula ACK e verifica UI/WS
Pubblica ACK dispositivo simulato:
```bash
mosquitto_pub -h localhost -p 1883 -t planty/plant-uno-01/ack -m '{"ts":"2026-01-10T10:20:02Z","cmd":"IRRIGATE","cmd_id":"sim-ack-1","result":"OK"}'
```

Verifica:
- Dashboard device page: campo ACK aggiornato.
- Oppure WS raw (stessa connessione) con messaggio `{"type":"ack", ...}`.
- Eventi backend:
```bash
curl -sS -X GET http://localhost:8000/events -H "Authorization: Bearer $TOKEN"
```
