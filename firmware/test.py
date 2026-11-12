import sys
import runpy
from unittest.mock import MagicMock

class Event:
    def __init__(self, key_number, pressed=True):
        self.key_number = key_number
        self.pressed = pressed
        self.released = not pressed

class FakeEvents:
    def __init__(self, script):
        self.script = list(script)
    def get(self):
        if not self.script:
            raise SystemExit
        return self.script.pop(0)

class FakeKeys:
    script = []
    def __init__(self, *a, **k):
        self.events = FakeEvents(FakeKeys.script)

class FakeEncoder:
    positions = []
    def __init__(self, *a, **k):
        self._last = 0
    @property
    def position(self):
        if FakeEncoder.positions:
            self._last = FakeEncoder.positions.pop(0)
        return self._last

def run(key_script, encoder_positions):
    FakeKeys.script = key_script
    FakeEncoder.positions = encoder_positions

    keypad = MagicMock(Keys=FakeKeys)
    rotaryio = MagicMock(IncrementalEncoder=FakeEncoder)
    kbd_mod = MagicMock()
    cc_mod = MagicMock()

    for name in ["board", "busio", "displayio", "i2cdisplaybus", "terminalio",
                 "usb_hid", "adafruit_displayio_ssd1306", "adafruit_display_text",
                 "adafruit_display_text.label", "adafruit_hid",
                 "adafruit_hid.keycode", "adafruit_hid.consumer_control_code"]:
        sys.modules[name] = MagicMock()
    sys.modules["keypad"] = keypad
    sys.modules["rotaryio"] = rotaryio
    sys.modules["adafruit_hid.keyboard"] = kbd_mod
    sys.modules["adafruit_hid.consumer_control"] = cc_mod

    try:
        runpy.run_path("code.py")
    except SystemExit:
        pass

    return kbd_mod.Keyboard.return_value, cc_mod.ConsumerControl.return_value

kbd, cc = run(
    key_script=[Event(0), None, Event(3), Event(6), None, None],
    encoder_positions=[0, 0, 0, 0, 2, 1],
)
print("keyboard:", kbd.send.mock_calls)
print("consumer:", cc.send.mock_calls)