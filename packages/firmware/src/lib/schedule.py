import ujson


class Schedule:
    __instance: Schedule | None = None

    _schedules: list[dict]

    def __init__(self, file_path: str = "/data/schedules.json") -> None:
        self.path = file_path
        self._schedules = []

    def load_schedules(self) -> bool:
        """
        Load the schedules from the JSON persistence store.

        :return: True if load was successful, False otherwise.
        """
        try:
            with open(self.path, "r") as f:
                data = ujson.load(f)
                if isinstance(data, list):
                    self._schedules = data
                    return True
                else:
                    print(f"Data in {self.path} is not a list.")
                    return False
        except Exception as e:  # noqa: BLE001
            print(f"Error loading schedules from {self.path}: {e}")
            return False

    def get_schedules(self) -> list[dict]:
        """
        Get the list of schedules.

        :return: List of schedule dictionaries.
        """
        return self._schedules

    def save_schedules(self, schedules: list[dict] | None = None) -> bool:
        """
        Save the schedules to the JSON persistence store.

        :param schedules: Optional list of schedules to save. If None, saves the current schedules.
        :return: True if save was successful, False otherwise.
        """
        if schedules is not None:
            self._schedules = schedules

        try:
            with open(self.path, "w") as f:
                ujson.dump(self._schedules, f)
            return True
        except Exception as e:  # noqa: BLE001
            print(f"Error saving schedules to {self.path}: {e}")
            return False

    @classmethod
    def create(cls, file_path: str = "/data/schedules.json") -> Schedule:
        if cls.__instance is None:
            cls.__instance = Schedule(file_path)
        return cls.__instance
