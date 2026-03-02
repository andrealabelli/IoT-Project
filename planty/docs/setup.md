# Setup end-to-end

## 1) Configurazione
- Copia `.env.example` (root) in `.env`.
- Copia:
  - `planty/firmware/arduino_uno/include/config.example.h` -> `config.h`
  - `planty/firmware/esp8266_bridge/include/secrets.example.h` -> `secrets.h`

## 2) Avvio stack
```bash
cd planty/infra
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

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

## 5) Verifica accettazione
1. UNO genera frame TEL + ACK con CRC valido.
2. ESP pubblica telemetry/ack MQTT e inoltra cmd con retry/timeout.
3. Backend salva eventi/telemetria, notifica Telegram e pusha WS.
4. Dashboard aggiorna live e mostra ack comando.
5. Nessun segreto in repo (`.env`, `secrets.h`, `config.h` ignorati).
