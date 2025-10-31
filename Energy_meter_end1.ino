#include <WiFi.h>
#include <PubSubClient.h>
#include "ACS712.h"
#include <ZMPT101B.h>

// WiFi credentials
const char* ssid = "qwerty";
const char* password = "12345678";

// Edge device IP (MQTT broker)
const char* mqtt_server = "192.168.x.xxx";  

WiFiClient espClient;
PubSubClient client(espClient);

#define RELAY_PIN 25

// Sensors
ACS712 ACS(34, 3.3, 4095, 70);
ZMPT101B voltageSensor(35, 50.0);

float current = 0;
float volt = 0;

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) message += (char)payload[i];
  
  if (message == "OFF") digitalWrite(RELAY_PIN, LOW);
  if (message == "ON") digitalWrite(RELAY_PIN, HIGH);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("node1")) {
      client.subscribe("ems/node1/control");
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Relay default ON

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

float readCurrent() {
  int noise = ACS.getNoisemV();
  float average = 0;
  for (int i = 0; i < 100; i++) average += ACS.mA_AC() - 330;
  float mA = average / 100.0;
  return (mA > 1) ? mA : 0;
}

float readVoltage() {
  float voltage = voltageSensor.getRmsVoltage();
  return (voltage > 50) ? voltage : 0;
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  current = readCurrent();
  volt =  readVoltage() ;

  // Build JSON payload
  String payload = "{\"voltage\":" + String(volt,2) +
                   ",\"current\":" + String(current,4) +"}";

  client.publish("ems/node1/data", payload.c_str());

  delay(10000); // publish every 10s
}
