#include <SPI.h>
#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

const int toggleBtn = 25;

int x = 10;
int y = 30;
int checkStatus = 1;
int lastButtonState = HIGH;
int smallTextSize = 1;
int largeTextSize = 2;
unsigned long idleTimeout = 5000;
unsigned long lastUpdate = 0;
unsigned long lastDebounceMs = 0;
const unsigned long debounceDelay = 200;

uint16_t COLOR_BROWN, COLOR_ORANGE;

void setup() {
  pinMode(toggleBtn, INPUT_PULLUP);
  Serial.begin(115200);
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_WHITE);
  tft.setFreeFont(&FreeSans9pt7b);
  tft.setTextSize(largeTextSize);
  tft.setCursor(x, y);
  tft.setTextColor(TFT_GREEN, TFT_WHITE);
  tft.println("Idle");
  lastUpdate = millis();
  COLOR_BROWN  = tft.color565(165, 42, 42);
  COLOR_ORANGE = tft.color565(255, 165, 0);
}


void drawStatus(const String& token, int status) {
  tft.setCursor(x, tft.height() - y);
  // draw checkout door
  if (status == 0) {
    tft.fillRect(120, 50, 120, 140, COLOR_BROWN);
    tft.drawRect(120, 50, 120, 140, TFT_BLACK);
    tft.fillCircle(200, 120, 6, TFT_YELLOW);
    tft.drawCircle(200, 120, 6, TFT_BLACK);
    tft.print(token);
    tft.setTextColor(TFT_RED);
    tft.print(" Checkout");
  } else if (status == 1) {
    // draw checkin
    tft.fillCircle(160, 120, 50, TFT_GREEN);
    tft.drawLine(140, 120, 155, 140, TFT_WHITE);
    tft.drawLine(155, 140, 185, 95, TFT_WHITE);
    tft.print(token);
    tft.setTextColor(TFT_GREEN);
    tft.print(" Checkin");
  } else {
    tft.fillCircle(160, 120, 50, TFT_BLUE);
    tft.fillCircle(140, 120, 8, TFT_WHITE);
    tft.fillCircle(160, 120, 8, TFT_WHITE);
    tft.fillCircle(180, 120, 8, TFT_WHITE);
    tft.print(token);
    tft.setTextColor(TFT_BLUE);
    tft.print(" Wait");
  }
}

void printData(String data) {
  int dy = 30;
  int start = 0;
  int dividerIndex;
  int fieldIndex = 0;
  String token;
  tft.setTextSize(smallTextSize);
  while ((dividerIndex = data.indexOf(',', start)) != -1) {
    String message = data.substring(start, dividerIndex);
    if (fieldIndex == 0) {
      token = message;
    }
    if (fieldIndex == 1) {
      drawStatus(token, message.toInt());
    } else {
      tft.setTextColor(COLOR_ORANGE, TFT_WHITE);
      tft.setCursor(x, y + dy);
      tft.println(message);
      Serial.println(message);
      dy += 30;
    }
    start = dividerIndex + 1;
    fieldIndex++;
  }
  String message = data.substring(start);
  tft.setCursor(x, y + dy);
  tft.println(message);
  Serial.println(message);
}

void loop() {
  tft.setTextSize(largeTextSize);
  int reading = digitalRead(toggleBtn);
  if (reading != lastButtonState) {
    lastDebounceMs = millis();

  }
  if ((millis() - lastDebounceMs) > debounceDelay) {
    static int stableState = HIGH;
    if (reading != stableState) {
      if (reading == HIGH && stableState == LOW) {
        checkStatus = 1 - checkStatus;
        tft.fillScreen(TFT_WHITE);
        tft.setCursor(x, y);
        tft.setTextColor(TFT_YELLOW, TFT_WHITE);
        tft.println("Mode toggled");
        drawStatus("---", checkStatus);
        Serial.printf("MODE:%d\n", checkStatus);
        lastUpdate = millis();
      }
      stableState = reading;
    }
  }
  lastButtonState = reading;

  if (Serial.available()) {
    String serialInput = Serial.readStringUntil('\n');
    serialInput.trim();
    tft.fillScreen(TFT_WHITE);
    tft.setCursor(x, y);
    tft.setTextColor(TFT_YELLOW, TFT_WHITE);
    tft.println("QR Code:");
    printData(serialInput);
    lastUpdate = millis();
  }
  if (millis() - lastUpdate > idleTimeout) {
    tft.fillScreen(TFT_WHITE);
    tft.setCursor(x, y);
    tft.setTextColor(TFT_GREEN, TFT_WHITE);
    tft.println("Idle");
    drawStatus("---", checkStatus);
    lastUpdate = millis();
  }
}