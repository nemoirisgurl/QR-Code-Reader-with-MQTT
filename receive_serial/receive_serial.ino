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

void drawStatus(int status){
  if (status == 0){
    tft.fillRect(110, 70, 100, 100, TFT_RED);
    tft.fillRect(150, 70, 10, 100, TFT_WHITE); 
  } else {
    tft.fillCircle(160, 120, 50, TFT_GREEN);
    tft.drawLine(140, 120, 155, 140, TFT_WHITE);
    tft.drawLine(155, 140, 185, 95, TFT_WHITE);
  }
}

void printData(String data) {
  int dy = 30;
  int start = 0;
  int dividerIndex;
  int fieldIndex = 0;
  tft.setTextSize(smallTextSize);
  while ((dividerIndex = data.indexOf(',', start)) != -1) {
    String message = data.substring(start, dividerIndex);
    if (fieldIndex == 2){
      drawStatus(message.toInt());
    } else {
      tft.setTextColor(TFT_ORANGE, TFT_WHITE);
      tft.setCursor(x, y + dy);
      tft.println(message);
      Serial.println(message);
      start = dividerIndex + 1;
      
    }
    dy += 30;
    fieldIndex++;
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
