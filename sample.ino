#include <TimerOne.h>

#define LED 7
#define thresholdDrop 35
#define refractoryTime 400  // мс

int prev = 0;
unsigned long lastBeat = 0;
int bpm = 0;

void setup() {
  Serial.begin(115200);
  Timer1.initialize(3000);
  Timer1.attachInterrupt(readECG);

  pinMode(LED, OUTPUT);
}

void readECG() {
  int raw = analogRead(A0);
  int val = map(raw, 0, 1023, 0, 255);

  int diff = val - prev;

  unsigned long now = millis();

  // Детекция R-пика по резкому падению
  if (diff < -thresholdDrop && (now - lastBeat) > refractoryTime) {
    if (lastBeat != 0) {
      unsigned long dt = now - lastBeat;
      bpm = 60000 / dt;
    }
    lastBeat = now;
    digitalWrite(LED, HIGH);
  } else {
    digitalWrite(LED, LOW);
  }

  prev = val;

  // отправляем сигнал и BPM
  Serial.print(val);
  Serial.print(",");
  Serial.println(bpm);
}

void loop() {}

