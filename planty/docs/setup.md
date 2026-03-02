# Setup

1. Copiare `.env.example` in `.env` e configurare valori.
2. Avvio stack:
   ```bash
   cd planty/infra
   docker compose up --build
   ```
3. Backend: http://localhost:8000/docs
4. Frontend: http://localhost:5173
5. Flash firmware:
   ```bash
   cd planty/firmware/esp32
   pio run -t upload
   ```
6. Verifica E2E:
   - register/login;
   - creare device da admin;
   - vedere telemetria live (<2s) su dettaglio device;
   - testare "Irriga ora" e controllare ack in `/events`;
   - simulare umidità bassa per notifiche Telegram.

## Note fisiche (NFR9/NFR10)
- Posizionare elettronica in box IP54 lontano da schizzi diretti.
- Isolare contatti pompa con guaina termorestringente.
- Tenere sensore terreno solo nella zona sondata (non completamente immerso).
- Ingombro target: box 12x8x5 cm + pompa esterna compatta.
