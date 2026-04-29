from typing import ClassVar, override

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class TRAPIConfig(BaseSettings):
    """Settings used for TRAPI handling."""

    biolink_version: str = "4.3.2"
    schema_version: str = "1.6.0"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        case_sensitive=False
    )

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Set the settings source priority."""
        return env_settings, init_settings


TRAPI_CONFIG = TRAPIConfig()
