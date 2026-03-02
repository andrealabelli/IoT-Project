# Firmware Arduino UNO

Gestisce sensori, stato pianta e pompa. Comunica con ESP8266 via UART con frame:

`$<BODY>*<CRC_XOR_HEX>\n`

- CRC = XOR di tutti i byte del BODY (tra `$` e `*`).
- Telemetria: `TEL,<deviceId>,<ts>,<tC>,<rh>,<soilRaw>,<soilPct>,<state>,<flags>`
- Comando: `CMD,<cmdId>,IRRIGATE,<ms>` oppure `CMD,<cmdId>,STATUS`
- ACK: `ACK,<cmdId>,OK` oppure `ACK,<cmdId>,ERR,<reason>`

## Configurazione
Copiare `include/config.example.h` in `include/config.h` e regolare pin/soglie/calibrazioni.
