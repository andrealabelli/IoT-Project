# Planty ESP32 Firmware

## Configurazione
Creare `src/config.h` (ignorato da git) con:

```cpp
#pragma once
#define WIFI_SSID "..."
#define WIFI_PASSWORD "..."
#define MQTT_HOST "192.168.1.10"
#define MQTT_PORT 1883
#define MQTT_USER ""
#define MQTT_PASSWORD ""
#define DEVICE_ID "plant-01"
#define PUBLISH_INTERVAL_MS 10000
#define SOIL_THRESHOLD 35
#define LOW_SOIL_SAMPLES 3
#define BAD_AIR_MINUTES 5
#define AIR_TEMP_MIN 15
#define AIR_TEMP_MAX 30
#define AIR_HUM_MIN 30
#define AIR_HUM_MAX 75
#define LOCKOUT_MS 180000
#define PUMP_DURATION_SECONDS 5
#define TEMP_OFFSET 0.0
#define HUM_OFFSET 0.0
#define SOIL_OFFSET 0.0
#define USE_DEEP_SLEEP false
```
