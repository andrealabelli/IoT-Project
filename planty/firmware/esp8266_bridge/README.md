# Firmware ESP8266 Bridge

Bridge Wi-Fi/MQTT <-> UART con Arduino UNO.

## Configurazione
Copiare `include/secrets.example.h` in `include/secrets.h` e impostare Wi-Fi/MQTT/deviceId.

## Funzioni
- reconnect Wi-Fi/MQTT
- parsing frame con CRC XOR
- publish telemetry/state/ack su MQTT
- inoltro comandi `irrigate`/`ping` verso UNO con timeout+retry
