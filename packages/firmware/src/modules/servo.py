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
        Điều khiển PWM cho Servo.
        """
        if 0 <= index < len(self._servos):
            duty = 0 if pulse_us == 0 else int((pulse_us / 20000) * 65535)
            self._servos[index].duty_u16(duty)

    async def drop(self, slot: str, quantity: int, timeout_per_pill: int = 8) -> bool:
        """
        Thực hiện nhả thuốc và kiểm tra cảm biến.
        Đã fix lỗi dội tín hiệu (bouncing) làm lọt khe logic.
        """
        slot_map = {"0-0": 0, "0-1": 1, "1-0": 2, "1-1": 3}
        servo_index = slot_map.get(slot)

        if servo_index is None:
            print(f"[ERROR] Invalid slot: {slot}")
            return False

        for i in range(quantity):
            # Chốt giá trị đếm hiện tại của cảm biến làm mốc ban đầu
            initial_count = self._states.drop_count
            
            start_time = time.ticks_ms()
            timeout_ms = timeout_per_pill * 1000

            # Kích hoạt xoay servo
            self.control(servo_index, 1300)

            pill_dropped = False
            while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
                # Dùng ">=" thay vì "==". Dù cảm biến bị nhiễu nhảy vọt từ 4 lên 7,
                # thì 7 >= 4 + 1 vẫn luôn luôn ĐÚNG -> Bắt tín hiệu hoàn hảo!
                if self._states.drop_count >= initial_count + 1:
                    pill_dropped = True
                    break
                await uasyncio.sleep(0.01)

            # Ngắt xung, dừng servo
            self.control(servo_index, 0)

            if not pill_dropped:
                print(
                    f"[ERROR] Slot {slot} timeout! Initial: {initial_count}, Current: {self._states.drop_count}"
                )
                return False

            print(f"[INFO] Slot {slot} dropped pill {i + 1}/{quantity}.")
            
            # Thời gian nghỉ cho viên thuốc kịp trôi xuống và servo ổn định
            await uasyncio.sleep(2.0)

        print(f"[SUCCESS] Slot {slot} successfully dropped {quantity} pills.")
        return True

    @classmethod
    def create(cls) -> "Servo":
        if cls._instance is None:
            cls._instance = Servo()
        return cls._instance