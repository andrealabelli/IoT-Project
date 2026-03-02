# Planty Architecture (Arduino UNO + ESP8266)

## Hardware split obbligatorio
- **Arduino UNO**: DHT22 + sensore umidità suolo + logica stato + scheduler irrigazione + controllo pompa.
- **ESP8266 NodeMCU**: Wi-Fi + MQTT + bridge seriale robusto verso UNO.

```text
[DHT22 + Soil + Pump]
        |
     Arduino UNO
 (state logic + lockout)
        | UART frame+CRC+ACK
     ESP8266 NodeMCU
        | MQTT
      Mosquitto
        |
     FastAPI backend ---- SQLite
        | WS push <=2s
      React dashboard
```

## Serial protocol UNO <-> ESP8266
Frame: `$<BODY>*<CRC>\n`
- CRC: XOR byte-per-byte del BODY (tra `$` e `*`) in HEX a 2 cifre.
- UNO -> ESP:
  - `TEL,<deviceId>,<ts>,<tC>,<rh>,<soilRaw>,<soilPct>,<state>,<flags>`
  - `ACK,<cmdId>,OK`
  - `ACK,<cmdId>,ERR,<reason>`
- ESP -> UNO:
  - `CMD,<cmdId>,IRRIGATE,<ms>`
  - `CMD,<cmdId>,STATUS`

## MQTT topics
- `planty/<deviceId>/telemetry`
- `planty/<deviceId>/state`
- `planty/<deviceId>/cmd/irrigate`
- `planty/<deviceId>/cmd/ping`
- `planty/<deviceId>/ack`

## FR/NFR mapping
- FR1/FR2/FR3 implementati su UNO + validazione stato lato backend.
- FR4 Telegram lato backend su stati critici.
- FR5 end-to-end command+ack (dashboard->backend->MQTT->ESP->UART->UNO e ritorno).
- FR6 refresh via ping/cmd STATUS.
- FR7 JWT login/register backend + frontend.
- NFR1 media mobile + offset sensori su UNO e offset lato backend.
- NFR2 reconnect MQTT/Wi-Fi, retry serial cmd, gestione fault.
- NFR3 websocket push telemetry/ack 1-2s.
