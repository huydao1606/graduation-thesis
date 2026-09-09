import time

from machine import Pin

from lib.pins import Pins
from lib.states import States


class Sensor:
    __instance: Sensor | None = None

    def __init__(self) -> None:
        self._states = States.create()

        pins = Pins.create()
        _ = pins.sensor_drop.irq(trigger=Pin.IRQ_FALLING, handler=self._drop_irq)
        _ = pins.sensor_check.irq(trigger=Pin.IRQ_FALLING, handler=self._check_irq)

    def _drop_irq(self, _pin: Pin) -> None:
        """
        Interrupt Service Routine (ISR) callback for the pill drop sensor pin.

        Debounce Mechanism:
            - Evaluates time delta using `time.ticks_diff()`.
            - Ignores consecutive noise triggers occurring within an 80ms window (`> 80ms`).
            - Increments `States.drop_count` and updates timestamp upon valid trigger.

        :param _pin: Pin instance triggering the hardware interrupt.
        :return: None
        """
        current_time: int = time.ticks_ms()

        if time.ticks_diff(current_time, self._states.drop_last_trigger_time) > 80:
            self._states.drop_count += 1
            self._states.drop_last_trigger_time = current_time
            print(
                f"\n[DROP SENSOR] Pill detected! Total count: {self._states.drop_count}"
            )

    def _check_irq(self, _pin: Pin) -> None:
        """
        Interrupt Service Routine (ISR) callback for the pill stock check sensor pin.

        Debounce Mechanism:
            - Evaluates time delta using `time.ticks_diff()`.
            - Ignores consecutive noise triggers occurring within an 80ms window (`> 80ms`).
            - Increments `States.check_count` and updates timestamp upon valid trigger.

        :param _pin: Pin instance triggering the hardware interrupt.
        :return: None
        """
        current_time: int = time.ticks_ms()

        if time.ticks_diff(current_time, self._states.check_last_trigger_time) > 80:
            self._states.check_count += 1
            self._states.check_last_trigger_time = current_time
            print(
                f"\n[CHECK SENSOR] Pill detected! Total count: {self._states.check_count}"
            )

    @classmethod
    def create(cls) -> Sensor:
        if cls.__instance is None:
            cls.__instance = Sensor()
        return cls.__instance
