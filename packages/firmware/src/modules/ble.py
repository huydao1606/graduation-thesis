import uasyncio
import ubluetooth
import ujson

from lib.config import load_config
from tasks.ble_handler import BLEHandler

_CONFIG_SERVICE_UUID = ubluetooth.UUID("ffaa5bd2-45cd-4512-bf35-c5d4276a0c7a")
_CHAR_RX_UUID = ubluetooth.UUID("3d8cffcb-69d3-41d3-8f9e-fafed0bcce6b")
_CHAR_TX_UUID = ubluetooth.UUID("09cbb497-1c8a-4ad6-b196-3459c1820a1a")


class BLE:
    __instance: BLE | None = None

    handle_rx: memoryview[int] | None = None
    handle_tx: memoryview[int] | None = None
    conn_handle: memoryview[int] | None = None
    _config: dict | None = None

    def __init__(self) -> None:
        config = load_config()
        self._config = config.get("device", {})

        self.rx_buffer = bytearray()
        self.send_lock = uasyncio.Lock()
        self.handler = BLEHandler(self)

        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        _ = self.ble.irq(self._irq)

        service = (
            _CONFIG_SERVICE_UUID,
            (
                (_CHAR_RX_UUID, 0x0008),  # WRITE
                (_CHAR_TX_UUID, 0x0002 | 0x0010),  # READ | NOTIFY
            ),
        )
        handles = self.ble.gatts_register_services((service,))
        self.handle_rx, self.handle_tx = handles[0]
        self.ble.gatts_set_buffer(self.handle_rx, 512, True)

    def start_advertising(self) -> None:
        """
        Construct GAP advertising payload and start broadcasting BLE presence.

        Payload Structure:
            - Flags AD Type (0x01): General Discoverable Mode & BR/EDR Not Supported.
            - Complete Local Name (0x09): Encoded device name string from configuration.
            - Complete List of 128-bit Service Class UUIDs (0x07): Service configuration UUID.

        :return: None
        """
        if not self.ble or self._config is None:
            return

        name = self._config.get("name", "Rozumari")

        payload = bytearray([0x02, 0x01, 0x06])
        name_bytes = name.encode("utf-8")
        payload.extend(bytearray([len(name_bytes) + 1, 0x09]) + name_bytes)
        uuid_bytes = bytes(_CONFIG_SERVICE_UUID)  # pyright: ignore[reportArgumentType]
        payload.extend(bytearray([len(uuid_bytes) + 1, 0x07]) + uuid_bytes)

        self.ble.gap_advertise(625000, adv_data=payload)  # pyright: ignore[reportCallIssue]
        print(f"Advertising as {name}...")

    def _irq(self, event: int, data: tuple) -> None:
        """
        Interrupt Request (IRQ) callback dispatcher handling BLE hardware events.

        Handled Events:
            - **Event 1 (_IRQ_CENTRAL_CONNECT)**:
                Stores connection handle, flushes RX buffer, and schedules the `on_connect` handler task.
            - **Event 2 (_IRQ_CENTRAL_DISCONNECT)**:
                Resets connection handle, flushes RX buffer, and schedules advertising restart task.
            - **Event 3 (_IRQ_GATTS_WRITE)**:
                Reads incoming characteristic data chunks into `rx_buffer` and schedules buffer processing
                when a newline delimiter (`\\n`) is encountered.

        :param event: Numeric identifier of the triggered BLE IRQ event.
        :param data: Tuple containing event-specific parameters from MicroPython BLE stack.
        :return: None
        """

        if event == 1:  # Connect
            print("Device connected")
            self.conn_handle = data[0]
            self.rx_buffer = bytearray()

            _ = uasyncio.create_task(self.handler.on_connect())
        elif event == 2:  # Disconnect
            print("Device disconnected")
            self.conn_handle = None
            self.rx_buffer = bytearray()
            _ = uasyncio.create_task(self._async_start_advertising())

        elif event == 3:  # Write
            if self.handle_rx is None:
                return

            _, val_handle = data
            if val_handle == self.handle_rx:
                chunk = self.ble.gatts_read(self.handle_rx)
                if chunk:
                    self.rx_buffer.extend(chunk)
                    if b"\n" in chunk:
                        _ = uasyncio.create_task(self._process_buffer())

    async def send_code(self, action: int, status: int = 0) -> None:
        """
        Pack Action (3 bits) and Status (5 bits) into a single byte transmission frame and notify connected client.

        Byte Framing Structure (1 Byte / 8 Bits):
            - **Bits 7..5 (3 bits)**: Action Code (`action & 0x07`).
            - **Bits 4..0 (5 bits)**: Status Code (`status & 0x1F`).
            - Bitwise Math: `packet_byte = ((action & 0x07) << 5) | (status & 0x1F)`

        Workflow:
            1. Packs inputs into a 1-byte payload.
            2. Acquires `send_lock` concurrency mutex.
            3. Writes byte payload to local GATT characteristic buffer (`handle_tx`).
            4. Triggers GATT notification push to connected client.

        :param action: Integer action code identifier (0 to 7).
        :param status: Integer status code or bitmasked payload parameter (0 to 31).
        :return: None
        """
        if not self.ble or self.conn_handle is None or self.handle_tx is None:
            print("Cannot send: Not connected")
            return

        packet_byte = bytes([((action & 0x07) << 5) | (status & 0x1F)])

        async with self.send_lock:
            self.ble.gatts_write(self.handle_tx, packet_byte)
            await uasyncio.sleep_ms(10)

            try:
                self.ble.gatts_notify(self.conn_handle, self.handle_tx, packet_byte)  # pyright: ignore[reportCallIssue]
            except TypeError:
                self.ble.gatts_notify(self.conn_handle, self.handle_tx)  # pyright: ignore[reportArgumentType]

            await uasyncio.sleep_ms(30)
            print(
                f"Sent 1 Byte: 0x{packet_byte.hex().upper()} (Action: {action}, Status: {status})"
            )

    def stop(self) -> None:
        """
        Stop GAP advertising, disconnect active central clients, and deactivate BLE radio interface.

        :return: None
        """
        if not self.ble:
            return
        self.ble.gap_advertise(0)
        if self.conn_handle is not None:
            try:
                _ = self.ble.gap_disconnect(self.conn_handle)
            except Exception:  # noqa: BLE001, S110
                pass
            self.conn_handle = None
        self.ble.active(False)

    async def _async_start_advertising(self) -> None:
        """
        Asynchronously delay and trigger advertising broadcast restart.

        :return: None
        """
        await uasyncio.sleep_ms(100)
        self.start_advertising()

    async def _process_buffer(self) -> None:
        """
        Parse accumulated UTF-8 text buffer into JSON command structures and execute handlers.

        :return: None
        """
        if not self.rx_buffer:
            return

        raw_str = self.rx_buffer.decode("utf-8", "ignore").strip()

        try:
            data = ujson.loads(raw_str)
            self.rx_buffer = bytearray()

            action = data.get("action")
            payload = data.get("payload", {})

            if action:
                await self.handler.handle_command(action, payload)

        except Exception:  # noqa: BLE001, S110
            pass

    @classmethod
    def create(cls) -> BLE:
        if cls.__instance is None:
            cls.__instance = BLE()
        return cls.__instance
