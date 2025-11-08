#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "webtool_frames.h"

constexpr int8_t OLED_RESET_PIN = -1;  // Using shared reset line on D1 mini shield.
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;

Adafruit_SSD1306 display(OLED_RESET_PIN);

constexpr uint8_t BITMAP_WIDTH = WEBTOOL_BITMAP_WIDTH;
constexpr uint8_t BITMAP_HEIGHT = WEBTOOL_BITMAP_HEIGHT;
constexpr size_t FRAME_COUNT = WebtoolFrames::FRAME_COUNT;

void haltWithError() {
  for (;;) {
    delay(10);
  }
}

void drawFrame(size_t index) {
  display.clearDisplay();
  const FrameDescriptor& frame = WebtoolFrames::FRAMES[index];
  display.drawBitmap(0, 0, frame.bitmap, BITMAP_WIDTH, BITMAP_HEIGHT, WHITE);
  display.display();
  Serial.print(F("Displayed frame: "));
  Serial.println(frame.name);
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
  const FrameDescriptor& frame = WebtoolFrames::FRAMES[frameIndex];
  if (now - lastChange >= frame.delay_ms) {
    frameIndex = (frameIndex + 1) % FRAME_COUNT;
    drawFrame(frameIndex);
    lastChange = now;
  }
}
