#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "front.h"
#include "right.h"
#include "back.h"
#include "left.h"

constexpr int8_t OLED_RESET_PIN = -1;  // Using shared reset line on D1 mini shield.
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;

Adafruit_SSD1306 display(OLED_RESET_PIN);

constexpr uint8_t BITMAP_WIDTH = 64;
constexpr uint8_t BITMAP_HEIGHT = 48;
constexpr uint32_t FRAME_DURATION_MS = 1000;

struct Frame {
  const uint8_t* bitmap;
  const char* name;
};

const Frame FRAMES[] = {
    {front, "front"},
    {right, "right"},
    {back, "back"},
    {left, "left"},
};
constexpr size_t FRAME_COUNT = sizeof(FRAMES) / sizeof(FRAMES[0]);

void haltWithError() {
  for (;;) {
    delay(10);
  }
}

void drawFrame(size_t index) {
  display.clearDisplay();
  display.drawBitmap(0, 0, FRAMES[index].bitmap, BITMAP_WIDTH, BITMAP_HEIGHT, WHITE);
  display.display();
  Serial.print(F("Displayed frame: "));
  Serial.println(FRAMES[index].name);
}

void setup() {
  Wire.begin();
  Serial.begin(115200);
  display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDRESS);
  drawFrame(0);
  Serial.println(F("OLED animation initialized."));
}

void loop() {
  static size_t frameIndex = 0;
  static uint32_t lastChange = millis();

  const uint32_t now = millis();
  if (now - lastChange >= FRAME_DURATION_MS) {
    frameIndex = (frameIndex + 1) % FRAME_COUNT;
    drawFrame(frameIndex);
    lastChange = now;
  }
}
