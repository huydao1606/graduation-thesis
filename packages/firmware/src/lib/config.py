import json as ujson


class Config:
    __instance: Config | None = None

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.config = self._load()

    def get(self, key: str, default: str | int | dict | None = None):
        return self.config.get(key, default)

    def set(self, key: str, value: str | int | dict) -> bool:
        self.config[key] = value
        try:
            with open(self.file_path, "w") as f:
                ujson.dump(self.config, f)
            return True
        except Exception as e:  # noqa: BLE001
            print(f"Error saving configuration to {self.file_path}: {e}")
            return False

    def _load(self) -> dict:
        with open(self.file_path, "r") as f:
            self.config = ujson.load(f)
        return self.config

    @classmethod
    def create(
        cls, file_path: str = "/data/config.json", force: bool = False
    ) -> Config:
        if cls.__instance is None or force:
            cls.__instance = cls(file_path)
        return cls.__instance
