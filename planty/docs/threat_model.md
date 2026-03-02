# Threat Model

- Asset: credenziali utente, token JWT, controllo pompa, dati telemetria.
- Rischi: furto token, comando non autorizzato, spoofing MQTT device.
- Mitigazioni:
  - password hash bcrypt;
  - JWT breve + refresh;
  - route protette con bearer token;
  - segreti in `.env`;
  - produzione dietro reverse proxy HTTPS + MQTT auth/TLS.
- Hardening consigliato: ACL MQTT per topic per-device, rotazione secret key, rate limiting login.
