#include <SPI.h>
#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

int x = 10;
int y = 30;
int smallTextSize = 1;
int largeTextSize = 2;

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_WHITE);
  tft.setTextSize(largeTextSize);
  tft.setCursor(x, y);
  tft.setTextColor(TFT_GREEN, TFT_WHITE);
  tft.println("Idle");
}

void printData(String data) {
  int dy = 30;
  int start = 0;
  int dividerIndex;
  tft.setTextSize(smallTextSize);
  while ((dividerIndex = data.indexOf(',', start)) != -1) {
    String message = data.substring(start, dividerIndex);
    tft.setTextColor(TFT_ORANGE, TFT_WHITE);
    tft.setCursor(x, y + dy);
    tft.println(message);
    Serial.println(message);
    start = dividerIndex + 1;
    dy += 30;
  }
  String message = data.substring(start);
  tft.setCursor(x, y + dy);
  tft.println(message);
  Serial.println(message);
}

void loop() {
  tft.setTextSize(largeTextSize);
  if (Serial.available()) {
    String serialInput = Serial.readStringUntil('\n');
    serialInput.trim();
    tft.fillScreen(TFT_WHITE);
    tft.setCursor(x, y);
    tft.setTextColor(TFT_YELLOW, TFT_WHITE);
    tft.println("QR Code:");
    printData(serialInput);
  }
}
