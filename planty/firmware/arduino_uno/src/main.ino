#include <Arduino.h>
#include <DHT.h>
#include "config.h"

enum PlantState { ST_OK, ST_NEEDS_WATER, ST_MOVE_PLANT, ST_FAULT };

DHT dht(DHT_PIN, DHT_TYPE);

float soilSamples[MOVING_WINDOW] = {0};
float tempSamples[MOVING_WINDOW] = {0};
float rhSamples[MOVING_WINDOW] = {0};
uint8_t sampleIdx = 0;
bool sampleFilled = false;

unsigned long lastTelemetry = 0;
unsigned long lastAutoCheck = 0;
unsigned long lastWatering = 0;
unsigned long badAirStart = 0;
uint8_t lowSoilCount = 0;
uint32_t cmdCounter = 0;

String rxLine;

uint8_t frameCrc(const String &frameNoDollarStar) {
  uint8_t c = 0;
  for (size_t i = 0; i < frameNoDollarStar.length(); i++) c ^= (uint8_t)frameNoDollarStar[i];
  return c;
}

String crcHex(uint8_t c) {
  char b[3];
  sprintf(b, "%02X", c);
  return String(b);
}

bool parseFrame(const String &line, String &body) {
  if (!line.startsWith("$") || line.indexOf('*') < 0) return false;
  int star = line.indexOf('*');
  body = line.substring(1, star);
  String rxCrc = line.substring(star + 1);
  rxCrc.trim();
  return rxCrc.equalsIgnoreCase(crcHex(frameCrc(body)));
}

void sendFrame(const String &body) {
  Serial.print("$");
  Serial.print(body);
  Serial.print("*");
  Serial.println(crcHex(frameCrc(body)));
}

float avg(float *arr, uint8_t len) {
  float s = 0; for (uint8_t i = 0; i < len; i++) s += arr[i];
  return s / len;
}

float soilPctFromRaw(int raw) {
  float pct = ((float)(SOIL_RAW_DRY - raw) / (SOIL_RAW_DRY - SOIL_RAW_WET)) * 100.0f;
  pct += SOIL_OFFSET;
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

PlantState evalState(float t, float rh, float soilPct) {
  if (isnan(t) || isnan(rh)) return ST_FAULT;
  if (soilPct < SOIL_LOW_THRESHOLD) lowSoilCount++; else lowSoilCount = 0;
  bool badAir = (t < TEMP_MIN || t > TEMP_MAX || rh < RH_MIN || rh > RH_MAX);
  if (badAir && badAirStart == 0) badAirStart = millis();
  if (!badAir) badAirStart = 0;
  if (lowSoilCount >= LOW_SOIL_SAMPLES_REQUIRED) return ST_NEEDS_WATER;
  if (badAirStart > 0 && millis() - badAirStart >= (unsigned long)BAD_AIR_MINUTES_REQUIRED * 60000UL) return ST_MOVE_PLANT;
  return ST_OK;
}

const char* stateTxt(PlantState st) {
  switch (st) {
    case ST_NEEDS_WATER: return "NEEDS_WATER";
    case ST_MOVE_PLANT: return "MOVE_PLANT";
    case ST_FAULT: return "SENSOR_FAULT";
    default: return "OK";
  }
}

void runPump(uint32_t ms) {
  digitalWrite(PUMP_PIN, HIGH);
  delay(ms);
  digitalWrite(PUMP_PIN, LOW);
  lastWatering = millis();
}

void publishTelemetry(bool emitStateOnly = false) {
  float t = dht.readTemperature() + TEMP_OFFSET;
  float rh = dht.readHumidity() + RH_OFFSET;
  int soilRaw = analogRead(SOIL_PIN);
  float soilPct = soilPctFromRaw(soilRaw);

  soilSamples[sampleIdx] = soilPct;
  tempSamples[sampleIdx] = t;
  rhSamples[sampleIdx] = rh;
  sampleIdx = (sampleIdx + 1) % MOVING_WINDOW;
  if (sampleIdx == 0) sampleFilled = true;

  uint8_t n = sampleFilled ? MOVING_WINDOW : sampleIdx;
  if (n == 0) n = 1;
  float tAvg = avg(tempSamples, n);
  float rhAvg = avg(rhSamples, n);
  float soilAvg = avg(soilSamples, n);

  PlantState st = evalState(tAvg, rhAvg, soilAvg);
  String flags = (st == ST_FAULT) ? "SENSOR_ERROR" : "OK";
  String body = "TEL," + String(DEVICE_ID) + "," + String(millis()) + "," + String(tAvg, 1) + "," + String(rhAvg, 1) + "," + String(soilRaw) + "," + String((int)soilAvg) + "," + String(stateTxt(st)) + "," + flags;
  if (!emitStateOnly) sendFrame(body);

  if (millis() - lastAutoCheck >= AUTO_INTERVAL_MS) {
    lastAutoCheck = millis();
    if (st == ST_NEEDS_WATER && millis() - lastWatering >= LOCKOUT_MS) {
      runPump(PUMP_DEFAULT_MS);
      sendFrame("ACK,AUTO_" + String(++cmdCounter) + ",OK");
    }
  }
}

void processCmd(const String &body) {
  if (!body.startsWith("CMD,")) return;
  int p1 = body.indexOf(',');
  int p2 = body.indexOf(',', p1 + 1);
  if (p2 < 0) return;
  String cmdId = body.substring(p1 + 1, p2);
  String rest = body.substring(p2 + 1);

  if (rest.startsWith("IRRIGATE")) {
    int p = rest.indexOf(',');
    uint32_t ms = PUMP_DEFAULT_MS;
    if (p > 0) ms = (uint32_t)rest.substring(p + 1).toInt();
    if (millis() - lastWatering < LOCKOUT_MS) {
      sendFrame("ACK," + cmdId + ",ERR,LOCKOUT");
      return;
    }
    runPump(ms);
    sendFrame("ACK," + cmdId + ",OK");
  } else if (rest == "STATUS") {
    publishTelemetry();
    sendFrame("ACK," + cmdId + ",OK");
  } else {
    sendFrame("ACK," + cmdId + ",ERR,UNKNOWN_CMD");
  }
}

void serialLoop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      String line = rxLine;
      rxLine = "";
      String body;
      if (parseFrame(line, body)) processCmd(body);
    } else if (c != '\r') {
      rxLine += c;
      if (rxLine.length() > 180) rxLine = "";
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  dht.begin();
}

void loop() {
  serialLoop();
  if (millis() - lastTelemetry >= TELEMETRY_INTERVAL_MS) {
    lastTelemetry = millis();
    publishTelemetry();
  }
}
