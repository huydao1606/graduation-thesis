import uasyncio
import ujson
from machine import Pin

from lib.api import Api
from tasks.sync_schedule import SyncSchedule

led = Pin("LED", Pin.OUT)


class Streaming:
    __instance: Streaming | None = None

    api: Api
    sync_schedule: SyncSchedule

    def __init__(self):
        self.api = Api.create()
        self.sync_schedule = SyncSchedule.create()

    async def _handle_payload(self, line: str) -> None:
        """
        Parse raw SSE payload lines and trigger hardware or software actions.

        :param line: Raw text line received from the streaming endpoint.
        :return: None
        """
        if not line or line.startswith(":keep-alive"):
            return

        if line.startswith("data:"):
            line = line[5:].strip()

        try:
            data = ujson.loads(line)
        except ValueError as e:
            print(f"Failed to parse JSON: {e}")
            return

        action = data.get("action")
        payload = data.get("payload")

        if action == "led":
            print(f"Setting LED state to: {payload}")
            led.value(int(payload))

        elif action == "sync_schedule":
            await self.sync_schedule.sync()

    async def start(self) -> None:
        """
        Start the continuous Server-Sent Events (SSE) streaming listener loop with exponential backoff logic.

        Detailed Workflow:
            1. **Stream Connection Setup**:
               - Invokes `self.api.stream()` to establish a long-lived HTTP SSE subscription connection to
                 the endpoint `/api/devices/subscribe`.
               - Registers `self._handle_payload` as the callback function to handle incoming streaming data chunks.
               - Sets a 30-second read timeout parameter to detect stalled or dropped socket connections.

            2. **Successful Stream Processing**:
               - When the connection maintains stability or completes gracefully, resets the connection backoff
                 delay parameter (`retry_delay`) to its base duration of 2 seconds.

            3. **Error Recovery & Reconnection Logic**:
               - Catches network, socket, or parsing exceptions thrown during streaming execution without crashing the device.
               - Prints an error diagnostic message containing the exception payload.
               - Suspends task execution via `uasyncio.sleep(retry_delay)` before attempting a reconnect.

            4. **Exponential Backoff Retry Calculation**:
               - Doubles `retry_delay` after each failure iteration (`retry_delay * 2`).
               - Caps the max backoff wait period at `max_delay` (60 seconds) to prevent infinite growth while conserving resources.

        :return: None
        :raises Exception: Internal stream or connection exceptions are caught, logged, and handled internally.
        """
        print(
            "[STARTUP] Streaming task initiated...\n",
            {"endpoint": "/api/devices/subscribe"},
        )

        retry_delay = 2
        max_delay = 60

        while True:
            try:
                await self.api.stream(
                    endpoint="/api/devices/subscribe",
                    callback=self._handle_payload,
                    timeout=30,
                )
                retry_delay = 2
            except Exception as e:  # noqa: BLE001
                print(f"Streaming error: {e}")

            print(f"Reconnecting in {retry_delay} seconds...")
            await uasyncio.sleep(retry_delay)

            retry_delay = min(retry_delay * 2, max_delay)

    @classmethod
    def create(cls) -> Streaming:
        if cls.__instance is None:
            cls.__instance = Streaming()
        return cls.__instance


if __name__ == "__main__":
    streaming = Streaming.create()
    uasyncio.run(streaming.start())
