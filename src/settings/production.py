from src.settings.app import AppSettings


class ProdAppSettings(AppSettings):
    class ConfigDict(AppSettings.ConfigDict):
        env_file = "prod.env"
        extra = "allow"
