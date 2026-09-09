import uasyncio

from lib.api import Api
from lib.schedule import Schedule
from lib.states import States
from lib.utils import get_current_time, print_table
from modules.servo import Servo
from modules.stepper import Stepper


class Schedules:
    __instance: "Schedules | None" = None

    api: Api
    servo: Servo
    stepper: Stepper
    schedule: Schedule
    states: States

    def __init__(self):
        self.api = Api.create()
        self.servo = Servo.create()
        self.stepper = Stepper.create()
        self.schedule = Schedule.create()
        self.states = States.create()

    async def start(self) -> None:
        print("[STARTUP] Schedules task initiated...\n")
        last_executed_time = ""

        while True:
            try:
                now = get_current_time()
                current_date: str = f"{now[0]:04d}-{now[1]:02d}-{now[2]:02d}"
                current_time: str = f"{now[3]:02d}:{now[4]:02d}"

                if current_time != last_executed_time:
                    last_executed_time = current_time
                    schedules = self.schedule.get_schedules()

                    print(f"\n[{current_date} {current_time}] Loaded schedules:")
                    print_table(schedules, keys=["id", "time", "date", "status"])

                    for schedule in schedules:
                        item_date = schedule.get("date")
                        item_time = schedule.get("time")
                        item_status = schedule.get("status", "pending")

                        if item_status != "pending":
                            continue

                        item_time = item_time[:5] if item_time else None

                        if item_time == current_time and (
                            not item_date or item_date == current_date
                        ):
                            schedule_id = schedule.get("id")
                            print(f"\nExecuting schedule ID {schedule_id}: {schedule}")

                            items = schedule.get("items", [])
                            schedule_success = True
                            failed_slot = []

                            # --- BƯỚC 1: NHẢ THUỐC BẰNG SERVO ---
                            for item in items:
                                slot = item.get("slot")
                                quantity = item.get("quantity", 1)

                                print(f"-> Dropping {quantity} pill(s) from slot {slot}")
                                success = await self.servo.drop(
                                    slot=slot, quantity=quantity
                                )

                                if not success:
                                    print(f"[ERROR] Slot {slot} failed! Ghi nhận lỗi và chạy tiếp ngăn sau.")
                                    schedule_success = False
                                    failed_slot.append(slot)
                                else:
                                    print(f"[INFO] Successfully dispensed slot {slot}")

                            # --- BƯỚC 2: QUY TRÌNH CƠ KHÍ & BÁO CÁO API ---
                            step_90_do = 512  # Số bước quay 90 độ (Chế độ Full-Step)

                            if schedule_success:
                                print("[SYSTEM] Đang mở ngăn kéo cho người dùng lấy thuốc...")
                                await self.stepper.drawer.move(step_90_do, delay_ms=2)
                                
                                print("[SYSTEM] Bắt đầu chờ bệnh nhân uống thuốc (Test: 15s)...")
                                await uasyncio.sleep(15) 
                                
                                print("[SYSTEM] Hết giờ! Đang đóng ngăn kéo...")
                                await self.stepper.drawer.move(-step_90_do, delay_ms=2)
                                await uasyncio.sleep(1) # Nghỉ 1 nhịp cho êm máy

                                print("[SYSTEM] Đang lật khay thu hồi thuốc dư...")
                                self.states.check_count = 0  # Reset bộ đếm cảm biến 2
                                await self.stepper.discard.move(step_90_do, delay_ms=2)
                                
                                # Chờ 3 giây để thuốc (nếu còn) rớt qua mắt thần
                                await uasyncio.sleep(3) 
                                
                                print("[SYSTEM] Trả khay lật về vị trí cũ...")
                                await self.stepper.discard.move(-step_90_do, delay_ms=2)

                                # Đánh giá tình trạng uống thuốc
                                missed_pills = self.states.check_count
                                if missed_pills > 0:
                                    notify_title = "Cảnh báo quên uống thuốc"
                                    notify_body = f"Bệnh nhân đã bỏ mót {missed_pills} viên thuốc ở khay!"
                                    notify_level = "warning"
                                    print(f"🚨 [CẢNH BÁO] {notify_body}")
                                else:
                                    notify_title = "Uống thuốc thành công"
                                    notify_body = f"Bệnh nhân đã lấy toàn bộ thuốc của lịch {schedule_id}."
                                    notify_level = "info"
                                    print(f"✅ [THÀNH CÔNG] {notify_body}")

                                # Gửi API và lưu trạng thái Thành công
                                _ = await self.api.post(
                                    "/api/notifications/send",
                                    data={
                                        "scheduleId": schedule_id,
                                        "level": notify_level,
                                        "title": notify_title,
                                        "body": notify_body,
                                        "payload": {"missed_pills": missed_pills},
                                    },
                                )
                                _ = await self.schedule.update_status(str(schedule_id), "completed")

                            else:
                                print("\n[SYSTEM] Phát hiện thiếu thuốc/kẹt thuốc! GIỮ ĐÓNG NGĂN KÉO.")
                                
                                # Lật khay để xả bỏ liều thuốc không hoàn chỉnh
                                print("[SYSTEM] Đang lật khay để xả bỏ các viên thuốc lẻ tẻ xuống khoang chứa...")
                                await self.stepper.discard.move(step_90_do, delay_ms=2)
                                
                                await uasyncio.sleep(3) 
                                
                                print("[SYSTEM] Đã dọn sạch khay! Trả khay về vị trí cũ...")
                                await self.stepper.discard.move(-step_90_do, delay_ms=2)

                                # Gửi API và lưu trạng thái Thất bại (Lỗi kẹt thuốc)
                                _ = await self.api.post(
                                    "/api/notifications/send",
                                    data={
                                        "scheduleId": schedule_id,
                                        "level": "error",
                                        "title": "Lỗi nhả thuốc - Đã hủy liều",
                                        "body": f"Lịch {schedule_id} bị lỗi cơ khí/kẹt thuốc. Đã xả bỏ liều uống không hoàn chỉnh.",
                                        "payload": {"failed_slots": failed_slot},
                                    },
                                )
                                _ = await self.schedule.update_status(str(schedule_id), "failed")
                                print(f"[FAILED] Schedule {schedule_id} failed.")

            except Exception as e:
                print(f"Error in schedule loop: {e}")

            now_after_task = get_current_time()
            seconds_to_next_minute = 60 - now_after_task[5]
            if seconds_to_next_minute <= 0:
                seconds_to_next_minute = 60

            await uasyncio.sleep(seconds_to_next_minute)

    @classmethod
    def create(cls) -> "Schedules":
        if cls.__instance is None:
            cls.__instance = Schedules()
        return cls.__instance