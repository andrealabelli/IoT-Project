#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <esp_task_wdt.h>
#include "config.h" // non-committed secrets/config

#define DHTPIN 4
#define DHTTYPE DHT22
#define SOIL_PIN 34
#define PUMP_PIN 26

DHT dht(DHTPIN, DHTTYPE);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

unsigned long lastPublish = 0;
unsigned long lastWatering = 0;
int lowSoilCount = 0;
int badAirMinutes = 0;

float readSoil() {
  int raw = analogRead(SOIL_PIN);
  float pct = map(raw, 3200, 1300, 0, 100);
  return constrain(pct + SOIL_OFFSET, 0, 100);
}

String computeState(float t, float h, float soil) {
  if (isnan(t) || isnan(h)) return "SENSOR_ERROR";
  if (soil < SOIL_THRESHOLD) lowSoilCount++; else lowSoilCount = 0;
  if (t < AIR_TEMP_MIN || t > AIR_TEMP_MAX || h < AIR_HUM_MIN || h > AIR_HUM_MAX) badAirMinutes++; else badAirMinutes = 0;
  if (lowSoilCount >= LOW_SOIL_SAMPLES) return "NEEDS_WATER";
  if (badAirMinutes >= BAD_AIR_MINUTES) return "MOVE_PLANT";
  return "OK";
}

void irrigate(int seconds, String cmdId) {
  digitalWrite(PUMP_PIN, HIGH);
  delay(seconds * 1000);
  digitalWrite(PUMP_PIN, LOW);
  String ack = "{\"command\":\"irrigate\",\"command_id\":\"" + cmdId + "\",\"success\":true,\"timestamp\":\"" + String(millis()) + "\"}";
  mqtt.publish((String("planty/") + DEVICE_ID + "/ack").c_str(), ack.c_str());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String t = String(topic);
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  if (t.endsWith("/cmd/irrigate")) {
    int duration = PUMP_DURATION_SECONDS;
    int idx = msg.indexOf("duration_seconds");
    if (idx > 0) duration = msg.substring(msg.indexOf(':', idx) + 1).toInt();
    irrigate(duration, "remote");
  }
  if (t.endsWith("/cmd/ping")) {
    String ack = "{\"command\":\"ping\",\"command_id\":\"remote\",\"success\":true}";
    mqtt.publish((String("planty/") + DEVICE_ID + "/ack").c_str(), ack.c_str());
  }
}

void connectWifiMqtt() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(callback);
  while (!mqtt.connected()) mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASSWORD);
  mqtt.subscribe((String("planty/") + DEVICE_ID + "/cmd/#").c_str());
}

void setup() {
  Serial.begin(115200);
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  dht.begin();
  esp_task_wdt_init(20, true);
  esp_task_wdt_add(NULL);
  connectWifiMqtt();
}

void loop() {
  esp_task_wdt_reset();
  if (!mqtt.connected() || WiFi.status() != WL_CONNECTED) connectWifiMqtt();
  mqtt.loop();

  if (millis() - lastPublish > PUBLISH_INTERVAL_MS) {
    lastPublish = millis();
    float t = dht.readTemperature() + TEMP_OFFSET;
    float h = dht.readHumidity() + HUM_OFFSET;
    float soil = readSoil();
    String state = computeState(t, h, soil);
    String payload = "{\"timestamp\":\"" + String(millis()) + "\",\"air_temperature\":" + String(t, 1) + ",\"air_humidity\":" + String(h, 1) + ",\"soil_moisture\":" + String(soil, 1) + ",\"state\":\"" + state + "\"}";
    mqtt.publish((String("planty/") + DEVICE_ID + "/telemetry").c_str(), payload.c_str());

    if (state == "NEEDS_WATER" && (millis() - lastWatering > LOCKOUT_MS)) {
      irrigate(PUMP_DURATION_SECONDS, "auto");
      lastWatering = millis();
    }

    if (USE_DEEP_SLEEP) {
      esp_deep_sleep((uint64_t)PUBLISH_INTERVAL_MS * 1000ULL);
    }
  }
}
