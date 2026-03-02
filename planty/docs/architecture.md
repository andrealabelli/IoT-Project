# Planty Architecture

Scelta MCU: **ESP32 DevKit** (Wi-Fi stabile, deep sleep, costo basso).

```text
[ESP32 + DHT22 + Soil + Pump]
   | MQTT telemetry/state/cmd/ack
[ Mosquitto ]
   | subscribed/publish
[ FastAPI Backend ] --SQLite--> [DB]
   | REST + WebSocket
[ React Dashboard ]
   | Telegram API
[ Notifications ]
```

## Flussi FR
- FR1: ESP32 legge DHT22 + terreno, filtra media mobile (firmware) e pubblica ogni intervallo.
- FR2: stato calcolato su device e ricalcolato nel backend (`calculate_state`).
- FR3: scheduler locale con lockout (`LOCKOUT_MS`) e trigger solo con suolo basso.
- FR4: backend invia Telegram su stati critici.
- FR5: comando remoto dashboard -> backend REST -> MQTT cmd irrigate -> ack.
- FR6: refresh via ping e lettura latest.
- FR7: register/login/logout/refresh con JWT e ruoli.

## NFR mapping
- NFR2: watchdog, reconnect Wi-Fi/MQTT, eventi persistenti.
- NFR3: websocket device stream (1s ping client).
- NFR4: publish interval + deep sleep opzionale.
- NFR7: modello dati multi-device (`devices`, `telemetry`).
