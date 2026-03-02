# Planty – Smart Pot IoT System

Implementazione end-to-end con **Arduino UNO + ESP8266 NodeMCU**:
- UNO: sensori/logica irrigazione/pompa
- ESP8266: bridge Wi-Fi/MQTT via seriale con CRC+ACK
- Backend FastAPI + JWT + MQTT + WebSocket
- Frontend React realtime

## Quickstart
```bash
cd planty/infra
docker compose up --build
```

Documentazione completa: `planty/docs/setup.md`.
