from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///argus.db"

    # JWT
    jwt_secret: str = "argus-hackathon-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Gemini
    google_api_key: str = ""
    gemini_eval_model: str = "gemini-2.0-flash"

    # Cards
    use_mock_cards: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Hedera Audit Logging
    use_hedera: bool = False
    hedera_account_id: str = ""
    hedera_private_key: str = ""
    hedera_topic_id: str = ""
    hedera_network: str = "testnet"

    class Config:
        env_file = ".env"
        env_prefix = "ARGUS_"


settings = Settings()
