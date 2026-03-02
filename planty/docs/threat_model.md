# Threat Model

- Asset: token JWT, comandi pompa, dati telemetria, credenziali Wi-Fi/MQTT.
- Superfici: API auth, MQTT broker, link UART, dashboard web.
- Minacce:
  - replay comando irrigazione;
  - accesso non autorizzato API;
  - spoofing topic MQTT;
  - corruzione frame seriali.
- Mitigazioni implementate:
  - JWT + password hash;
  - command_id/ack e controllo stato lockout lato UNO;
  - frame seriale con delimitatori + CRC XOR;
  - retry con timeout su ESP8266;
  - segreti fuori repo (`.env`, `secrets.h`).
- Mitigazioni consigliate produzione:
  - TLS/ACL su MQTT;
  - HTTPS reverse-proxy;
  - rate limit login;
  - rotazione secret key.
