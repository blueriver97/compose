import os
import logging
from typing import Any, Tuple
import yaml
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str


class GenerateConfig(BaseModel):
    duration: int
    transactions: int
    insert_rate: float
    update_rate: float
    delete_rate: float


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(self, field: Any, field_name: str) -> Tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        yaml_file = os.getenv("YAML_FILE", "./settings.yaml")
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Config file '{yaml_file}' not found. Using defaults or environment variables.")
            return {}
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return {}


class DatagenConfig(BaseSettings):
    database: DatabaseConfig
    generate: GenerateConfig
    tables: list[str]

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
        )
