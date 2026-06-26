from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelPricing:
    input_usd_per_million: float
    output_usd_per_million: float

    def __init__(self, input_usd_per_million: float, output_usd_per_million: float) -> None:
        self.input_usd_per_million = input_usd_per_million
        self.output_usd_per_million = output_usd_per_million


PRICING: dict[str, ModelPricing] = {
    "claude-opus-4-8": ModelPricing(input_usd_per_million=5.0, output_usd_per_million=25.0),
    "claude-sonnet-4-6": ModelPricing(input_usd_per_million=3.0, output_usd_per_million=15.0),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"

    anthropic_api_key: str = ""
    model_legal: str = "claude-sonnet-4-6"
    model_banking: str = "claude-sonnet-4-6"
    model_menu: str = "claude-opus-4-8"

    registry_base_url: str = "https://recherche-entreprises.api.gouv.fr"
    registry_timeout_seconds: float = 3.0

    database_url: str = "sqlite:///./onboarding.db"
    cors_origins: str = "http://localhost:5173"

    cost_cap_eur: float = 0.50
    usd_to_eur_rate: float = 0.92

    amplitude_api_key: str = ""

    uploads_directory: str = "uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


def compute_cost_eur(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model)
    if pricing is None:
        return 0.0
    usd = (
        input_tokens / 1_000_000 * pricing.input_usd_per_million
        + output_tokens / 1_000_000 * pricing.output_usd_per_million
    )
    return round(usd * settings.usd_to_eur_rate, 6)
