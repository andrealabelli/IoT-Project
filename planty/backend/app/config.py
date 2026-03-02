from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Planty API"
    secret_key: str = Field("change-me-in-env", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    sqlite_url: str = Field("sqlite:///./planty.db", alias="SQLITE_URL")
    mqtt_broker: str = Field("mosquitto", alias="MQTT_BROKER")
    mqtt_port: int = Field(1883, alias="MQTT_PORT")
    mqtt_username: str | None = Field(None, alias="MQTT_USERNAME")
    mqtt_password: str | None = Field(None, alias="MQTT_PASSWORD")
    mqtt_base_topic: str = Field("planty", alias="MQTT_BASE_TOPIC")
    telegram_bot_token: str | None = Field(None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(None, alias="TELEGRAM_CHAT_ID")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
