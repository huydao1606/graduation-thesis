from machine import Pin

from lib.pins import Pins


class RGB:
    __instance: RGB | None = None
    led_r: Pin
    led_g: Pin
    led_b: Pin

    def __init__(self) -> None:
        pins = Pins.create()
        self.led_r = pins.led_r
        self.led_g = pins.led_g
        self.led_b = pins.led_b

        self.set_color(0, 0, 0)

    def set_color(self, r: int, g: int, b: int) -> None:
        """
        Set binary output state across Red, Green, and Blue LED channels.

        Truth Table / Digital Logic:
            - Any value `> 0` sets the respective Pin state to HIGH (`1`).
            - Any value `<= 0` sets the respective Pin state to LOW (`0`).

        :param r: Red channel intensity state (> 0 for ON, 0 for OFF).
        :param g: Green channel intensity state (> 0 for ON, 0 for OFF).
        :param b: Blue channel intensity state (> 0 for ON, 0 for OFF).
        :return: None
        """

        self.led_r.value(1 if r > 0 else 0)
        self.led_g.value(1 if g > 0 else 0)
        self.led_b.value(1 if b > 0 else 0)

    @classmethod
    def create(cls) -> RGB:
        if cls.__instance is None:
            cls.__instance = RGB()
        return cls.__instance
