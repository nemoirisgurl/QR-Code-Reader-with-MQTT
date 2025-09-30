#include <TFT_eSPI.h> 

TFT_eSPI tft = TFT_eSPI();

String message = "";

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);

  tft.setCursor(10, 30);
  tft.println("Waiting for QR Data...");
}

void loop(){
  if (Serial.available()) {
    message = Serial.readStringUntil('\n');
    tft.fillScreen(TFT_BLACK);
    tft.setCursor(10, 30);
    tft.setTextColor(TFT_YELLOW, TFT_BLACK);
    tft.println("Scanned Data:");

    tft.setCursor(10, 60);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.println(message);
  } 
}