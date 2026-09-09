import uasyncio

from lib.api import Api
from lib.schedule import Schedule
from lib.utils import get_current_time, print_table
from modules.servo import Servo
from modules.stepper import Stepper


class Schedules:
    __instance: Schedules | None = None

    api: Api

    servo: Servo
    stepper: Stepper

    schedule: Schedule

    _led_timer_task: uasyncio.Task | None = None

    def __init__(self):
        """
        Initialize the Schedules instance with hardware peripherals and file path.

        :param path: File path storing the JSON schedule database.
        """

        self.api = Api.create()

        self.servo = Servo.create()
        self.stepper = Stepper.create()

        self.schedule = Schedule.create()

    async def start(self) -> None:
        """
        Start the primary asynchronous event loop that monitors and executes pending schedules.

        Detailed Workflow:
            1. **Time Tracking & Loop Synchronization**:
               - Continuously queries the real-time clock via `get_current_time()`.
               - Formats current date (`DD/MM/YYYY`) and time (`HH:MM`).
               - Prevents duplicate executions within the same minute by tracking `last_executed_time`.

            2. **Schedule Resolution**:
               - Reads stored schedule records from `self.path` using `_read_schedule()`.
               - Prints an formatted status table to the output console.
               - Filters for items with a `"pending"` status matching the current time and (optional) date.

            3. **Execution & Hardware Feedback**:
               - Triggers visual LED feedback (Yellow: `(1, 1, 0)`) during processing.
               - Sequentially iterates through scheduled items, driving the servo mechanism (`self.servo.drop`)
                 for specified slot indices and pill quantities.
               - Aborts execution immediately if any slot drop action fails.

            4. **State Persistence & Completion Visuals**:
               - Sets post-execution LED feedback:
                 - **Green `(0, 1, 0)`**: Successful execution.
                 - **Red `(1, 0, 0)`**: Failed execution or error exception.
               - Automatically turns off the LED after a 10-second timeout.

            5. **Adaptive Sleep**:
               - Calculates remaining seconds until the next exact minute boundary (`60 - current_second`)
                 to minimize CPU usage while keeping precision timing.

        :return: None
        :raises Exception: Catches and logs runtime exceptions without terminating the main loop.
        """
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

                            if self._led_timer_task and not self._led_timer_task.done():
                                _ = self._led_timer_task.cancel()

                            items = schedule.get("items", [])
                            schedule_success = True
                            failed_slot = []

                            for item in items:
                                slot = item.get("slot")
                                quantity = item.get("quantity", 1)

                                print(
                                    f"-> Dropping {quantity} pill(s) from slot {slot}"
                                )
                                success = await self.servo.drop(
                                    slot=slot, quantity=quantity
                                )

                                if not success:
                                    print(
                                        f"[ERROR] Slot {slot} failed! Aborting schedule {schedule_id}."
                                    )
                                    schedule_success = False
                                    failed_slot.append(slot)
                                    break
                                else:
                                    print(f"[INFO] Successfully dispensed slot {slot}")

                            step = 512
                            await self.stepper.drawer.move(step, delay_ms=2)
                            await uasyncio.sleep(2)
                            await self.stepper.drawer.move(-step, delay_ms=2)
                            await uasyncio.sleep(2)

                            if schedule_success:
                                _ = await self.api.post(
                                    "/api/notifications/send",
                                    data={
                                        "scheduleId": schedule_id,
                                        "level": "info",
                                        "title": "Schedule Completed",
                                        "body": f"Schedule {schedule_id} completed successfully.",
                                        "payload": {},
                                    },
                                )
                                _ = await self.schedule.update_status(
                                    str(schedule_id), "completed"
                                )
                                print(
                                    f"[SUCCESS] Schedule {schedule_id} completed successfully."
                                )
                            else:
                                _ = await self.api.post(
                                    "/api/notifications/send",
                                    data={
                                        "scheduleId": schedule_id,
                                        "level": "error",
                                        "title": "Schedule Failed",
                                        "body": f"Schedule {schedule_id} failed to complete.",
                                        "payload": {"failed_slots": failed_slot},
                                    },
                                )
                                _ = await self.schedule.update_status(
                                    str(schedule_id), "failed"
                                )
                                print(f"[FAILED] Schedule {schedule_id} failed.")

            except Exception as e:  # noqa: BLE001
                print(f"Error in schedule loop: {e}")

            now_after_task = get_current_time()
            seconds_to_next_minute = 60 - now_after_task[5]
            if seconds_to_next_minute <= 0:
                seconds_to_next_minute = 60

            await uasyncio.sleep(seconds_to_next_minute)

    @classmethod
    def create(cls) -> Schedules:
        if cls.__instance is None:
            cls.__instance = Schedules()
        return cls.__instance
