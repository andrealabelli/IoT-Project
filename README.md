# Planty – Smart Pot IoT System

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Implementazione end-to-end con **Arduino UNO + ESP8266 NodeMCU**:
- UNO: sensori/logica irrigazione/pompa
- ESP8266: bridge Wi-Fi/MQTT via seriale con CRC+ACK
- Backend FastAPI + JWT + MQTT + WebSocket
- Frontend React realtime

## Quickstart
```bash
cp planty/.env.example planty/.env
cd planty/infra
docker compose --env-file ../.env up --build
```

Porte/URL default:
- Mosquitto MQTT: `1883`
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

Documentazione completa: `planty/docs/setup.md`.

Nota: ESP32 non è target principale; eventuali file ESP32 sono mantenuti solo come legacy.
