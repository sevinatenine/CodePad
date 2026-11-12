import time

import adafruit_displayio_ssd1306
import board
import busio
import displayio
import i2cdisplaybus
import keypad
import rotaryio
import terminalio
import usb_hid
from adafruit_display_text import label
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)
MOD = Keycode.COMMAND  # Use Keycode.CONTROL on Windows/Linux

displayio.release_displays()
i2c = busio.I2C(scl=board.D5, sda=board.D4)

# Might be 0x3D but I will need to test on hardware
bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(bus, width=128, height=32)

group = displayio.Group()
title = label.Label(terminalio.FONT, text="CodePad", x=2, y=8)
status = label.Label(terminalio.FONT, text="Ready", x=2, y=24)

group.append(title)
group.append(status)
display.root_group = group

STATUS_TIMEOUT = 2.0
status_set_at = 0

def show(text):
    global status_set_at
    status.text = text[:21]
    status_set_at = time.monotonic()

keys = keypad.Keys(
    (board.D3, board.D6, board.D7, board.D8, board.D9, board.D10, board.D2),
    value_when_pressed=False,
    pull=True,
    interval=0.02,
)

SHORTCUTS = {
    0: ("Copy",       (MOD, Keycode.C)),
    1: ("Paste",      (MOD, Keycode.V)),
    2: ("Cut",        (MOD, Keycode.X)),
    3: ("Undo",       (MOD, Keycode.Z)),
    4: ("Redo",       (MOD, Keycode.SHIFT, Keycode.Z)),
    5: ("Save",       (MOD, Keycode.S)),
}
ENCODER_BUTTON = 6

# Rotary encoder controls volume, click is mute
encoder = rotaryio.IncrementalEncoder(board.D0, board.D1)
last_position = encoder.position

while True:
    position = encoder.position
    delta = position - last_position
    if delta:
        code = (ConsumerControlCode.VOLUME_INCREMENT if delta > 0
                else ConsumerControlCode.VOLUME_DECREMENT)
        for _ in range(abs(delta)):
            cc.send(code)
        last_position = position
        show("Volume " + ("+" if delta > 0 else "-"))

    event = keys.events.get()
    if event and event.pressed:
        n = event.key_number
        if n == ENCODER_BUTTON:
            cc.send(ConsumerControlCode.MUTE)
            show("Mute")
        elif n in SHORTCUTS:
            name, combo = SHORTCUTS[n]
            kbd.send(*combo)
            show(name)

    if status.text != "Ready" and time.monotonic() - status_set_at > STATUS_TIMEOUT:
        status.text = "Ready"