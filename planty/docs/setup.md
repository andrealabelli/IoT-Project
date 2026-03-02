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
