import uasyncio
import ujson

from lib.utils import get_current_time, print_table
from modules.rgb import RGB
from modules.servo import Servo


class Schedules:
    __instance: Schedules | None = None

    path: str
    servo: Servo
    rgb: RGB
    _led_timer_task: uasyncio.Task | None = None

    def __init__(self, path: str = "data/schedules.json"):
        """
        Initialize the Schedules instance with hardware peripherals and file path.

        :param path: File path storing the JSON schedule database.
        """

        self.path = path
        self.servo = Servo.create()
        self.rgb = RGB.create()

    async def _set_color_with_timeout(
        self, r: int, g: int, b: int, timeout: int = 10
    ) -> None:
        """
        Set the RGB LED color and automatically turn it off after a specified timeout.

        :param r: Red component intensity (0 or 1).
        :param g: Green component intensity (0 or 1).
        :param b: Blue component intensity (0 or 1).
        :param timeout: Time duration in seconds before turning off the LED.
        :return: None
        """
        if self._led_timer_task and not self._led_timer_task.done():
            _ = self._led_timer_task.cancel()

        self.rgb.set_color(r, g, b)

        async def _turn_off_after_delay():
            try:
                await uasyncio.sleep(timeout)
                self.rgb.set_color(0, 0, 0)
            except uasyncio.CancelledError:
                pass

        self._led_timer_task = uasyncio.create_task(_turn_off_after_delay())

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
               - Updates and persists the schedule state (`"completed"` or `"failed"`) via `_update_schedule_status()`.
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
        last_executed_time = ""

        while True:
            try:
                now = get_current_time()
                current_date: str = f"{now[2]:02d}/{now[1]:02d}/{now[0]}"
                current_time: str = f"{now[3]:02d}:{now[4]:02d}"

                if current_time != last_executed_time:
                    last_executed_time = current_time
                    schedules = self._read_schedule()

                    print(f"\n[{current_time}] Loaded schedules:")
                    print_table(schedules, keys=["id", "time", "date", "status"])

                    for schedule in schedules:
                        item_date = schedule.get("date")
                        item_time = schedule.get("time")
                        item_status = schedule.get("status", "pending")

                        if item_status != "pending":
                            continue

                        if item_time == current_time and (
                            not item_date or item_date == current_date
                        ):
                            schedule_id = schedule.get("id")
                            print(f"\nExecuting schedule ID {schedule_id}: {schedule}")

                            if self._led_timer_task and not self._led_timer_task.done():
                                _ = self._led_timer_task.cancel()
                            self.rgb.set_color(1, 1, 0)

                            items = schedule.get("items", [])
                            schedule_success = True

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
                                    break
                                else:
                                    print(f"[INFO] Successfully dispensed slot {slot}")

                            new_status = "completed" if schedule_success else "failed"
                            self._update_schedule_status(schedule_id, new_status)

                            if schedule_success:
                                print(
                                    f"[SUCCESS] Schedule {schedule_id} completed successfully."
                                )
                                await self._set_color_with_timeout(0, 1, 0, timeout=10)
                            else:
                                print(f"[FAILED] Schedule {schedule_id} failed.")
                                await self._set_color_with_timeout(1, 0, 0, timeout=10)

            except Exception as e:  # noqa: BLE001
                print(f"Error in schedule loop: {e}")
                await self._set_color_with_timeout(1, 0, 0, timeout=10)

            now_after_task = get_current_time()
            seconds_to_next_minute = 60 - now_after_task[5]
            if seconds_to_next_minute <= 0:
                seconds_to_next_minute = 60

            await uasyncio.sleep(seconds_to_next_minute)

    def _read_schedule(self) -> list:
        """
        Read and deserialize the schedules list from the JSON persistence store.

        :return: List of schedule dictionaries or empty list if read fails.
        """

        try:
            with open(self.path, "r") as f:
                data = ujson.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:  # noqa: BLE001
            print(f"Error reading file {self.path}: {e}")
            return []

    def _update_schedule_status(self, schedule_id: str, new_status: str) -> None:
        """
        Update the execution status of a specific schedule ID and persist back to JSON.

        :param schedule_id: Unique identifier of the target schedule.
        :param new_status: New status string ('completed' or 'failed').
        :return: None
        """

        try:
            schedules = self._read_schedule()
            for item in schedules:
                if item.get("id") == schedule_id:
                    item["status"] = new_status
                    break

            with open(self.path, "w") as f:
                ujson.dump(schedules, f)
            print(f"[DB] Updated schedule {schedule_id} status to '{new_status}'")
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] Failed to update schedule status: {e}")

    @classmethod
    def create(cls) -> Schedules:
        if cls.__instance is None:
            cls.__instance = Schedules()
        return cls.__instance
