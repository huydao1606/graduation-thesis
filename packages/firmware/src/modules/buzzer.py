import time

from machine import Pin

from lib.pins import Pins


class Buzzer:
    __instance: Buzzer | None = None

    pin: Pin

    def __init__(self) -> None:
        pins = Pins.create()
        self.pin = pins.buzzer
        self.off()

    def on(self) -> None:
        self.pin.value(0)

    def off(self) -> None:
        self.pin.value(1)

    @classmethod
    def create(cls) -> Buzzer:
        if cls.__instance is None:
            cls.__instance = Buzzer()
        return cls.__instance


if __name__ == "__main__":
    buzzer = Buzzer.create()

    while True:
        buzzer.on()
        time.sleep(1)
        buzzer.off()
        time.sleep(1)
