/*
 *  The sketch controls a four button block with RGB leds under each button as well as reads three other buttons via
 *  analog in pins.
 *
 *  It communicates about the current state, and receives updates to the color state via serial over USB.
 */

// Button Grounds
const int buttonMatrix[] = { 2, 4, 6, 8 };

// LED Grounds
const int ledGnd[] = { 3, 5, 7, 12 };

// RGB pins
const int ledPwr[] = { 9, 10, 11 };

// Analog Buttons, not part of 4 button device.
//   Doorbell, Ctrl Black, Ctrl Red
const int analogButton[] = { 0, 1, 2 };
const boolean analogInvert[] = { false, false, true };

// Colour definitions
//   white:  true, true, true
//   red:    true, false, false
//   green:  false, true, false
//   blue:   false, false, true
//   yellow: true, true, false
//   dark:   false, false, false

// 0, 1, 2, 3 - Four Button Block
// 4, 5, 6 - Analog Buttons (red, black, doorbell)
boolean buttonState[] = { false, false, false, false, false, false, false };

boolean buttonColor[4][3] = { {false, false, false},
                              {false, false, false},
                              {false, false, false},
                              {false, false, false} };

void setButtonColor(int led, boolean color[3])
{
  for (int i = 0; i < 3; i++)
    buttonColor[led][i] = color[i];
}

void setup()
{
  // Switch Grounds
  for (int i = 0; i < 4; i++) {
    pinMode(buttonMatrix[i], INPUT_PULLUP);
  }

  // Led grounds
  for (int i = 0; i < 4; i++) {
    pinMode(ledGnd[i], OUTPUT);
  }

  // RGB pins
  for (int i = 0; i < 3; i++) {
    pinMode(ledPwr[i], OUTPUT);
  }

  runDiagnostic();

  // Serial if you need it
  Serial.begin(115200);
  Serial.setTimeout(100);  // Never block reads more than 100 milliseconds

  reportState();
}

void serialEvent() {

  if (Serial.available() < 1)
    return;

  // 15 bytes per color update.
  //   All Off: 000:000:000:000
  //   All On:  111:111:111:111

  char buffer[15];

  if (Serial.readBytes(buffer, 15) != 15) {
    // If we timed out trying to read the data, there was an error, throw
    // away what we read as it's probably garbage.
    reportState();
    return;
  }

  int i = 0;

  // Parse colors for the 4 buttons
  for (int b = 0; b < 4; b++) {
    boolean color[3];

    // Parse the 3 colors for each button RGB
    for (int c = 0; c < 3; c++) {
      color[c] = (buffer[i++] == '1');
    }
    setButtonColor(b, color);

    // Skip the ':' seperator.
    if (b < 3)
      i++;
  }

  reportState();
}

void loop() {
  boolean stateChanged = false;

  // Cycle through our digital buttons looking for a change.
  for (int i = 0; i < 4; i++) {

    // Read the button, and invert value (LOW for pushed).Â
    boolean buttonRead = !digitalRead(buttonMatrix[i]);

    // If that button changed, remember it, and report it.
    if (buttonState[i] != buttonRead) {
      buttonState[i] = buttonRead;
      stateChanged = true;
    }
  }

  // Cycle through our analog buttons looking for a change.
  for (int i = 0; i < 3; i++) {
    int value = analogRead(analogButton[i]);

    // value ranges between 0 - 1023. We expect it to be near one extreme or the other
    // to represent button pushed.
    boolean buttonRead = value > 512;

    // Some buttons go low when pushed, not high. Invert results.
    buttonRead = buttonRead ^ analogInvert[i];

    if (buttonState[i+4] != buttonRead) {
      buttonState[i+4] = buttonRead;
      stateChanged = true;
    }
  }

  if (stateChanged) {
    reportState();

    if (buttonState[0] && buttonState[1] && buttonState[2] && buttonState[3])
      runDiagnostic();
  }

  // Redraw our colors.
  ledColor(buttonColor);
}

void reportState() {
    Serial.print("{ ");

    Serial.print("\"buttons\": [");
    for (int i = 0; i < 7; i++) {
      Serial.print(buttonState[i]);
      if (i < 6)
        Serial.print(", ");
    }
    Serial.print("], ");

    Serial.print("\"colors\": [");
    // Write out each LED.
    for (int i = 0; i < 4; i++) {
      Serial.print('"');
      // Write each Color. Red, Green, Blue.
      for (int j = 0; j < 3; j++) {
        Serial.print(buttonColor[i][j]);
        if (j < 2)
          Serial.print(",");
      }
      Serial.print('"');

      if (i < 3)
        Serial.print(", ");
    }

    Serial.print("] }\n");
}

void runDiagnostic()
{
  boolean flashColors[5][4][3] = { { {true, true, true},
                                     {true, true, true},
                                     {true, true, true},
                                     {true, true, true} },

                                   { {true, false, false},
                                     {true, false, false},
                                     {true, false, false},
                                     {true, false, false} },

                                   { {false, true, false},
                                     {false, true, false},
                                     {false, true, false},
                                     {false, true, false} },

                                   { {false, false, true},
                                     {false, false, true},
                                     {false, false, true},
                                     {false, false, true} },

                                   { {true, false, false},
                                     {false, true, false},
                                     {false, false, true},
                                     {true, true, false} } };

  for (int i = 0; i < 5; i++) {
    unsigned long endTime = millis() + 400;
    while (millis() < endTime) {
      ledColor(flashColors[i]);
    }
  }
}


void ledColor(boolean buttonColor[4][3])
{
  // Process each LED.
  for (int i = 0; i < 4; i++) {
    // Write each color for the current led, Red, Green, Blue
    for (int j = 0; j < 3; j++) {
      if (buttonColor[i][j])
        analogWrite(ledPwr[j], 255);
      else
        analogWrite(ledPwr[j], 0);
    }

    // Light up the relevant LED.
    digitalWrite(ledGnd[i], LOW);
    delayMicroseconds(1100);
    digitalWrite(ledGnd[i], HIGH);
  }
}

