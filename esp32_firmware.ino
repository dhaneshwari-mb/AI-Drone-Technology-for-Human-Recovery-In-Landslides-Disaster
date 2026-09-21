#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>

// Replace with your Network Details
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// DHT Sensor Config
#define DHTPIN 4          // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11     // DHT 11 or DHT 22
DHT dht(DHTPIN, DHTTYPE);

WebServer server(80);

void setup() {
  Serial.begin(115200);
  dht.begin();
  
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Setup Routes
  server.on("/", HTTP_GET, []() {
    server.send(200, "text/plain", "ESP32 Sensor Server is Running.");
  });

  server.on("/temperature", HTTP_GET, []() {
    // Read temperature & humidity
    float t = dht.readTemperature();
    float h = dht.readHumidity();

    // Check if reading failed
    if (isnan(t) || isnan(h)) {
      server.send(500, "application/json", "{\"success\": false, \"error\": \"Failed to read from DHT sensor!\"}");
      return;
    }

    // Build JSON string
    String jsonStr = "{";
    jsonStr += "\"success\": true, ";
    jsonStr += "\"temperature\": " + String(t) + ", ";
    jsonStr += "\"humidity\": " + String(h);
    jsonStr += "}";

    // Set CORS headers for local testing
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", jsonStr);
  });

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  delay(2);
}
