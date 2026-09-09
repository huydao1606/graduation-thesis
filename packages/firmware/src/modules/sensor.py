import time

from machine import Pin

from lib.pins import Pins
from lib.states import States


class Sensor:
    __instance: "Sensor | None" = None

    def __init__(self) -> None:
        self._states = States.create()
        pins = Pins.create()

        # ====================================================================
        # [SENSOR 1] CẢM BIẾN NHẢ THUỐC (DISPENSE SENSOR)
        # -> Vị trí vật lý: Lắp dưới cụm 4 phễu Servo.
        # -> Nhiệm vụ: Đếm số lượng viên thuốc rơi từ các ống tuýp xuống ngăn kéo.
        # -> Được gọi bởi: servo.py (Để biết đã rớt đủ liều lượng mục tiêu chưa).
        # ====================================================================
        self.sensor_dispense = pins.sensor_drop
        self.sensor_dispense.irq(trigger=Pin.IRQ_FALLING, handler=self._dispense_irq)

        # ====================================================================
        # [SENSOR 2] CẢM BIẾN THU HỒI / KIỂM TRA (LEFTOVER SENSOR)
        # -> Vị trí vật lý: Lắp ở dưới khe đáy của khay người già lấy thuốc.
        # -> Nhiệm vụ: Đếm số viên thuốc rớt xuống khoang chứa rác khi lật khay.
        # -> Được gọi bởi: schedules.py (Để báo cáo số thuốc quên uống lên App).
        # ====================================================================
        self.sensor_leftover = pins.sensor_check
        self.sensor_leftover.irq(trigger=Pin.IRQ_FALLING, handler=self._leftover_irq)

    def _dispense_irq(self, _pin: Pin) -> None:
        """Ngắt IRQ cho Cảm biến 1 (Nhả thuốc)"""
        current_time: int = time.ticks_ms()

        # Cơ chế Debounce 80ms: Lọc nhiễu tránh 1 viên thuốc xẹt qua bị đếm thành 2
        if time.ticks_diff(current_time, self._states.drop_last_trigger_time) > 80:
            self._states.drop_count += 1
            self._states.drop_last_trigger_time = current_time
            print(f"\n💊 [SENSOR 1 - NHẢ THUỐC] Đã rớt viên thứ: {self._states.drop_count}")

    def _leftover_irq(self, _pin: Pin) -> None:
        """Ngắt IRQ cho Cảm biến 2 (Thu hồi thuốc thừa)"""
        current_time: int = time.ticks_ms()

        # Cơ chế Debounce 80ms
        if time.ticks_diff(current_time, self._states.check_last_trigger_time) > 80:
            self._states.check_count += 1
            self._states.check_last_trigger_time = current_time
            print(f"\n⚠️ [SENSOR 2 - THU HỒI] Phát hiện viên thuốc thừa thứ: {self._states.check_count}")

    @classmethod
    def create(cls) -> "Sensor":
        if cls.__instance is None:
            cls.__instance = Sensor()
        return cls.__instance