/*
 * 
 * Solar Car IV Sensor Measurements
 * SPI Communication w/ RPI
 * Ryan Wans 2023
 * 
 */

#include <Arduino.h>

// Get and sanatize current reading
float readCurrent(int pin, float correction) {
  float currentValue = analogRead(pin);
  currentValue = (currentValue - 512)*5/1024/0.04-0.04;
  currentValue = abs(currentValue + correction);
  return currentValue;
}

float readMotorVoltage() {
  // LOW = 3.64, HIGH = 4.64
  float voltageValue = analogRead(3);
  voltageValue = voltageValue * (5.0 / 1023.0);
  return voltageValue;
}

float readSolarVoltage() {
  // LOW = 0.00, HIGH = 4.50
  float voltageValue = analogRead(4);
  voltageValue = voltageValue * (5.0 / 1023.0);
  return voltageValue;
}

void sendData() {
  float motorIV = readCurrent(0, 0.41);
  float solarIV = readCurrent(1, 0.28);
  float accsyIV = readCurrent(2, 0.28);
  float motorVV = readMotorVoltage();
  float solarVV = readSolarVoltage();
  
  String msg = String(motorIV) + ";" + String(solarIV) + ";" + String(accsyIV) + ";" + String(motorVV) + ";" + String(solarVV);
  Serial.println(msg);
}

void setup() {
  Serial.begin(9600);
  Serial.println("ALIVE");
}

void loop() {
  // Check for incoming request for data
  if(Serial.available() > 0) {
    // Parse incoming data
    String data = Serial.readStringUntil('\n');
    if(data == "PING") {
      // Confirm that Arduino is alive if necessary
      Serial.println("PONG");
    } else if(data == "?") {
      // Send sensor data
      sendData();
      Serial.println("DONE");
    } else {
      Serial.println("Invalid entry.");
    }
  }
  
  // Timing delay
  delay(100);
}
