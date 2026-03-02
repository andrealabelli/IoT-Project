#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

WiFiClient wifi;
PubSubClient mqtt(wifi);
String serialLine;

struct PendingCmd {
  String cmdId;
  String cmd;
  unsigned long sentAt;
  bool waiting;
} pending = {"", "", 0, false};

uint8_t frameCrc(const String &s) { uint8_t c=0; for (size_t i=0;i<s.length();i++) c ^= (uint8_t)s[i]; return c; }
String crcHex(uint8_t c){ char b[3]; sprintf(b, "%02X", c); return String(b); }

void sendFrame(const String &body){ Serial.print("$"); Serial.print(body); Serial.print("*"); Serial.println(crcHex(frameCrc(body))); }

bool parseFrame(const String &line, String &body){
  if (!line.startsWith("$") || line.indexOf('*') < 0) return false;
  int star=line.indexOf('*');
  body=line.substring(1, star);
  String rx=line.substring(star+1); rx.trim();
  return rx.equalsIgnoreCase(crcHex(frameCrc(body)));
}

void publishAck(const String &cmd, const String &result, const String &reason="") {
  StaticJsonDocument<256> doc;
  doc["ts"] = millis();
  doc["cmd"] = cmd;
  doc["result"] = result;
  doc["cmd_id"] = pending.cmdId;
  if (reason.length()) doc["reason"] = reason;
  char out[256];
  serializeJson(doc, out);
  mqtt.publish((String("planty/") + DEVICE_ID + "/ack").c_str(), out, true);
}

void handleUnoBody(const String &body){
  if (body.startsWith("TEL,")) {
    // TEL,<deviceId>,<ts>,<tC>,<rh>,<soilRaw>,<soilPct>,<state>,<flags>
    int idx[9];
    int pos = 0;
    for (int i=0;i<9;i++){ idx[i] = body.indexOf(',', pos); pos = idx[i] + 1; if (idx[i] < 0) return; }
    String ts = body.substring(idx[1]+1, idx[2]);
    String t = body.substring(idx[2]+1, idx[3]);
    String rh = body.substring(idx[3]+1, idx[4]);
    String soilPct = body.substring(idx[5]+1, idx[6]);
    String state = body.substring(idx[6]+1, idx[7]);
    String flags = body.substring(idx[7]+1);

    StaticJsonDocument<256> doc;
    doc["ts"] = ts;
    doc["t_c"] = t.toFloat();
    doc["rh"] = rh.toFloat();
    doc["soil_pct"] = soilPct.toInt();
    doc["state"] = state;
    JsonArray arr = doc.createNestedArray("flags");
    arr.add(flags);
    char out[256]; serializeJson(doc, out);
    mqtt.publish((String("planty/") + DEVICE_ID + "/telemetry").c_str(), out);
    mqtt.publish((String("planty/") + DEVICE_ID + "/state").c_str(), out);
  } else if (body.startsWith("ACK,")) {
    // ACK,<cmdId>,OK|ERR[,reason]
    int a = body.indexOf(',');
    int b = body.indexOf(',', a+1);
    int c = body.indexOf(',', b+1);
    String cmdId = body.substring(a+1, b);
    String result = (c > 0) ? body.substring(b+1, c) : body.substring(b+1);
    String reason = (c > 0) ? body.substring(c+1) : "";
    if (pending.waiting && cmdId == pending.cmdId) {
      publishAck(pending.cmd, result, reason);
      pending.waiting = false;
    }
  }
}

void serialLoop(){
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      String line = serialLine; serialLine = "";
      String body;
      if (parseFrame(line, body)) handleUnoBody(body);
    } else if (c != '\r') {
      serialLine += c;
      if (serialLine.length() > 200) serialLine = "";
    }
  }
}

void connectWifi(){
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void mqttCb(char* topic, byte* payload, unsigned int len){
  String msg;
  for (unsigned int i=0;i<len;i++) msg += (char)payload[i];
  StaticJsonDocument<256> doc;
  deserializeJson(doc, msg);
  String cmdId = doc["command_id"] | String(millis());

  String top = String(topic);
  if (top.endsWith("/cmd/irrigate")) {
    int ms = (doc["duration_seconds"] | 5) * 1000;
    pending = {cmdId, "IRRIGATE", millis(), true};
    sendFrame("CMD," + cmdId + ",IRRIGATE," + String(ms));
  } else if (top.endsWith("/cmd/ping")) {
    pending = {cmdId, "STATUS", millis(), true};
    sendFrame("CMD," + cmdId + ",STATUS");
  }
}

void connectMqtt(){
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(mqttCb);
  while (!mqtt.connected()) {
    if (mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASSWORD)) {
      mqtt.subscribe((String("planty/") + DEVICE_ID + "/cmd/#").c_str());
    } else delay(1000);
  }
}

void setup(){
  Serial.begin(115200);
  connectWifi();
  connectMqtt();
}

void loop(){
  connectWifi();
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();
  serialLoop();

  if (pending.waiting && millis() - pending.sentAt > 3000) {
    if (millis() - pending.sentAt < 9000) {
      pending.sentAt = millis();
      if (pending.cmd == "IRRIGATE") sendFrame("CMD," + pending.cmdId + ",IRRIGATE,5000");
      else sendFrame("CMD," + pending.cmdId + ",STATUS");
    } else {
      publishAck(pending.cmd, "ERR", "TIMEOUT");
      pending.waiting = false;
    }
  }
}
