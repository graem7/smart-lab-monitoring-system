#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Wi-Fi
const char* ssid = "tmz";
const char* password = "12345678";

// Flask Server URL
const char* serverName = "http://192.168.43.168:5000/data";

// Sensor pins
#define LDR1_PIN 2      // First LDR
#define LED1_PIN 18      // LED controlled by first LDR
#define LDR2_PIN 4      // Second LDR
#define LED2_PIN 16      // LED controlled by second LDR
#define PIR_PIN 13       // PIR motion sensor
#define DHT_PIN 23       // DHT22 humidity sensor
#define GREEN_LED_PIN 26 // Green LED for motion detection
#define ONE_WIRE_BUS 14  // DS18B20 temperature sensors

DHT dht(DHT_PIN, DHT11);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  
  
  pinMode(LDR1_PIN, INPUT);
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LDR2_PIN, INPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  
  dht.begin();
  sensors.begin();
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("Connected!");
}

void loop() {

  int ldrValue1 = analogRead(LDR1_PIN);
  Serial.print("LDR1 Value: ");
  Serial.println(ldrValue1);
  
  if (ldrValue1 < 512) {
    digitalWrite(LED1_PIN, HIGH);
    Serial.println("LDR1 - Dark, LED1 ON");
  } else {
    digitalWrite(LED1_PIN, LOW);
    Serial.println("LDR1 - Light, LED1 OFF");
  }

  // Read LDR 2 and control LED 2 separately
  int ldrValue2 = analogRead(LDR2_PIN);
  Serial.print("LDR2 Value: ");
  Serial.println(ldrValue2);
  
  if (ldrValue2 < 512) {
    digitalWrite(LED2_PIN, HIGH);
    Serial.println("LDR2 - Dark, LED2 ON");
  } else {
    digitalWrite(LED2_PIN, LOW);
    Serial.println("LDR2 - Light, LED2 OFF");
  }

  // PIR Motion Sensor
  int motionDetected = digitalRead(PIR_PIN);
  if (motionDetected == HIGH) {
    Serial.println("Motion Detected");
    for (int i = 0; i < 4; i++) {
      digitalWrite(GREEN_LED_PIN, HIGH);
      delay(200);
      digitalWrite(GREEN_LED_PIN, LOW);
      delay(200);
    }
  } else {
    digitalWrite(GREEN_LED_PIN, LOW);
  }
  
  // DS18B20 Temperature Sensors
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);


  // DHT22 Humidity Sensor
  float humidity = dht.readHumidity();
  if (isnan(humidity)) {
    Serial.println("Failed to read humidity from DHT sensor!");
  } else {
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  }


  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    // Send all data separately
    String payloads[5] = {
      "{\"sensor\":\"ldr_data1\", \"value\":" + String(ldrValue1) + "}",
      "{\"sensor\":\"ldr_data2\", \"value\":" + String(ldrValue2) + "}",
      "{\"sensor\":\"pir_data\", \"value\":" + String(motionDetected) + "}",
      "{\"sensor\":\"humidity_data\", \"value\":" + String(humidity) + "}",
      "{\"sensor\":\"temperature_data\", \"value\":" + String(tempC) + "}"
    };

    for (String payload : payloads) {
      int httpResponseCode = http.POST(payload);
      Serial.println("Response: " + String(httpResponseCode));
    }

    http.end();
  }
delay(2000);
}


