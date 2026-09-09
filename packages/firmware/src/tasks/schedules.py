import time

import uasyncio

from lib.schedule import Schedule
from lib.utils import get_current_time, print_table
from modules.servo import Servo


class Schedules:
    _instance = None

    def __init__(self) -> None:
        self.servo = Servo.create()
        self.schedule = Schedule.create()

    async def start(self, schedules_data: list | None = None) -> None:
        print("[STARTUP] Schedules task active...\n")
        last_time = ""

        while True:
            try:
                now = get_current_time()
                cur_date = f"{now[0]:04d}-{now[1]:02d}-{now[2]:02d}"
                cur_time = f"{now[3]:02d}:{now[4]:02d}"

                if cur_time != last_time:
                    last_time = cur_time

                    schedules = (
                        schedules_data
                        if schedules_data is not None
                        else self.schedule.get_schedules()
                    )

                    sec = now[5] if len(now) > 5 else 0
                    print(
                        f"\n[SCHEDULE] [{cur_date} {cur_time}:{sec:02d}] Check schedules..."
                    )
                    print_table(schedules, keys=["id", "date", "time", "status"])

                    for item_sch in schedules:
                        if item_sch.get("status", "pending") != "pending":
                            continue

                        sch_time = (item_sch.get("time") or "")[:5]
                        sch_date = item_sch.get("date")

                        if sch_time == cur_time and (
                            not sch_date or sch_date == cur_date
                        ):
                            sch_id = item_sch.get("id")
                            items = item_sch.get("items", [])
                            print(f"\n---> EXECUTE SCHEDULE {sch_id}")

                            all_success = True

                            for item in items:
                                slot = item.get("slot")
                                qty = item.get("quantity", 1)

                                print(
                                    f"[SCHEDULE] Gọi Servo nhả Slot '{slot}' x {qty} viên..."
                                )
                                success = await self.servo.drop(slot=slot, quantity=qty)

                                if not success:
                                    all_success = False
                                    break
                                await uasyncio.sleep(1.0)

                            if all_success:
                                print(f"[SCHEDULE] Lịch {sch_id} đã nhả đủ thuốc!")
                                item_sch["status"] = "completed"
                                _ = await self.schedule.update_status(
                                    str(sch_id), "completed"
                                )
                            else:
                                print(f"[SCHEDULE] Lịch {sch_id} thất bại!")
                                item_sch["status"] = "failed"
                                _ = await self.schedule.update_status(
                                    str(sch_id), "failed"
                                )

            except Exception as e:  # noqa: BLE001
                print(f"[SCHEDULE] Error: {e}")

            # Tính toán chính xác ms còn lại đến giây tiếp theo để chống trôi thời gian
            ms_to_next_second = 1000 - (time.ticks_ms() % 1000)
            await uasyncio.sleep_ms(ms_to_next_second)

    @classmethod
    def create(cls) -> Schedules:
        if cls._instance is None:
            cls._instance = Schedules()
        return cls._instance
