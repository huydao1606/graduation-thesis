import time

import uasyncio

from lib.pins import Pins
from lib.states import States


class Servo:
    _instance = None

    def __init__(self) -> None:
        self._states = States.create()

        pins = Pins.create()
        self._servos = pins.servos

    def control(self, index: int, pulse_us: int) -> None:
        """
        Set PWM pulse width in microseconds for a targeted servo index.

        PWM Duty Conversion Logic:
            - Pulse cycle period = 20,000 µs (50 Hz standard servo frequency).
            - 16-bit resolution scale range = 0 to 65535 (`2^16 - 1`).
            - Formula: `duty_u16 = (pulse_us / 20000) * 65535`
            - Setting `pulse_us = 0` sets `duty_u16 = 0` (stops signal).

        :param index: Target servo motor array index.
        :param pulse_us: High-state pulse duration in microseconds (0 to disable).
        :return: None
        """

        if 0 <= index < len(self._servos):
            duty = 0 if pulse_us == 0 else int((pulse_us / 20000) * 65535)
            self._servos[index].duty_u16(duty)

    async def drop(self, slot: str, quantity: int, timeout_per_pill: int = 8) -> bool:
        """
        Dispense a target quantity of pills from a specified slot with active IR sensor verification.

        Detailed Workflow:
            1. **Slot Mapping**:
               - Maps matrix string coordinates (`"0-0"`, `"0-1"`, `"1-0"`, `"1-1"`) to physical servo indices (0 to 3).
               - Aborts execution if the provided slot string is unmapped.

            2. **Per-Pill Dispensing Loop**:
               - Resets state counter `self._states.drop_count = 0` before initiating each pill drop iteration.
               - Actuates target servo motor using a fixed pulse width (`1300` µs).

            3. **Sensor Detection Polling**:
               - Polls hardware drop IR interrupt triggers continuously using 10ms non-blocking polling loops.
               - Evaluates elapsed execution time against `timeout_per_pill` duration.
               - Disables servo pulse immediately (`pulse_us = 0`) upon detecting a pill drop or timeout condition.

            4. **Error Handling & Inter-Pill Delay**:
               - Aborts immediately and returns `False` if IR sensor fails to register a drop within the timeout period.
               - Applies a 1-second stabilization pause between consecutive pill drops.

        :param slot: Matrix slot location identifier string (e.g., `"0-0"`).
        :param quantity: Total number of pills required to drop.
        :param timeout_per_pill: Maximum wait time in seconds per pill before timing out.
        :return: `True` if all pills dispense successfully, `False` otherwise.
        """
        slot_map = {"0-0": 0, "0-1": 1, "1-0": 2, "1-1": 3}
        servo_index = slot_map.get(slot)

        if servo_index is None:
            print(f"[ERROR] Invalid slot: {slot}")
            return False

        for i in range(quantity):
            self._states.drop_count = 0
            start_time = time.ticks_ms()
            timeout_ms = timeout_per_pill * 1000

            self.control(servo_index, 1300)

            pill_dropped = False
            while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
                if self._states.drop_count >= 1:
                    pill_dropped = True
                    break
                await uasyncio.sleep(0.01)

            self.control(servo_index, 0)

            if not pill_dropped:
                print(
                    f"[ERROR] Slot {slot} timeout! Target: 1, Current count: {self._states.drop_count}"
                )
                return False

            print(f"[INFO] Slot {slot} dropped pill {i + 1}/{quantity}.")
            await uasyncio.sleep(1.0)

        print(f"[SUCCESS] Slot {slot} successfully dropped {quantity} pills.")
        return True

    @classmethod
    def create(cls) -> Servo:
        if cls._instance is None:
            cls._instance = Servo()
        return cls._instance
